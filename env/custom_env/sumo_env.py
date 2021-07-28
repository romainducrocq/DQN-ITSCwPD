# https://sumo.dlr.de/pydoc/

from __future__ import absolute_import, print_function

from .utils import \
    SUMO_PARAMS

import sys
import json
import random
import numpy as np
from itertools import permutations

SUMO_HOME = "./venv/sumo/"

sys.path.append(SUMO_HOME + 'tools')

from sumolib import net  # noqa
import traci  # noqa


class SumoEnv:
    SUMO_ENV = "./env/custom_env/"

    @staticmethod
    def pretty_print(d):
        print(json.dumps(d, sort_keys=True, indent=4))

    @staticmethod
    def arg_max(_list):
        return max(range(len(_list)), key=lambda i: _list[i])

    @staticmethod
    def arg_min(_list):
        return min(range(len(_list)), key=lambda i: _list[i])

    @staticmethod
    def clip(min_clip, max_clip, x):
        return max(min_clip, min([max_clip, x])) if min_clip < max_clip else x

    def __init__(self, gui=False, log=False, rnd=(False, False)):
        self.args = SUMO_PARAMS

        self.gui = False
        self.config = self.args["config"]
        self.data_dir = self.SUMO_ENV + "data/" + self.config + "/"

        self.net = net.readNet(self.data_dir + self.config + ".net.xml")
        self.tl_ids = [tl.getID() for tl in self.net.getTrafficLights()]

        self.tl_net = self.gen_tl_net()
        """
        SumoEnv.pretty_print(self.tl_net)
        exit()
        """

        self.route_net = self.gen_route_net()
        """
        SumoEnv.pretty_print(self.route_net)
        exit()
        """

        self.generate_route_file(gen=False)
        traci.start(self.set_params())

        self.tl_logic = self.gen_tl_logic()
        """
        SumoEnv.pretty_print(self.tl_logic)
        exit()
        """

        self.tl_signals = self.gen_tl_signals()
        """
        SumoEnv.pretty_print(self.tl_signals)
        exit()
        """

        self.flow_logic = self.gen_flow_logic()
        """
        SumoEnv.pretty_print(self.flow_logic)
        exit()
        """

        self.gui = gui
        self.log = log
        self.rnd = rnd

        self.veh_n = 0
        self.flow = []
        self.con_p_rate = 1.
        self.ctrl_con_p_rate = 1.
        self.veh_n_p_hour = []

        """
        self.update_flow_logic()
        SumoEnv.pretty_print(self.flow_logic)
        # [print(f) for f in self.flow]
        exit()
        """

        self.params = self.set_params()

        self.ep_count = 0

    def set_params(self):
        params = [
            SUMO_HOME + "bin/sumo" + ("-gui" if self.gui else ""), "-c",
            self.data_dir + self.config + ".sumocfg",
            "--tripinfo-output", self.data_dir + "tripinfo.xml",
            "--time-to-teleport", str(self.args["steps"]),
            "--waiting-time-memory", str(self.args["steps"])
        ]

        if self.gui:
            params += [
                "--delay", str(self.args["delay"]),
                "--start", "true", "--quit-on-end", "true",
                "--gui-settings-file", self.SUMO_ENV + "data/" + self.config + "/gui-settings.cfg"
            ]

        return params

    ####################################################################################################################
    ####################################################################################################################

    def start(self):
        self.generate_route_file()
        traci.start(self.params)

    def stop(self):
        traci.close()
        sys.stdout.flush()

    def simulation_reset(self):
        self.stop()
        self.start()

    def simulation_step(self):
        traci.simulationStep()

    def reset(self):
        raise NotImplementedError

    def step(self, action):
        raise NotImplementedError

    def obs(self):
        raise NotImplementedError

    def rew(self):
        raise NotImplementedError

    def done(self):
        raise NotImplementedError

    def info(self):
        return {} if not self.log else self.log_info()

    def is_simulation_end(self):
        return traci.simulation.getMinExpectedNumber() == 0

    def get_current_time(self):
        return traci.simulation.getCurrentTime() // 1000

    ####################################################################################################################
    ####################################################################################################################

    # traffic light

    def get_phase(self, tl_id):
        return traci.trafficlight.getPhase(tl_id)

    def get_ryg_state(self, tl_id):
        return traci.trafficlight.getRedYellowGreenState(tl_id)

    def set_phase(self, tl_id, phase):
        traci.trafficlight.setPhase(tl_id, phase)

    def set_phase_duration(self, tl_id, dur):
        traci.trafficlight.setPhaseDuration(tl_id, dur)

    def yield_tl_vehs(self, tl_id):
        for lane_id in self.get_tl_incoming_lanes(tl_id):
            for veh_id in self.get_lane_veh_ids(lane_id):
                yield veh_id

    # lane

    def get_lane_veh_ids(self, lane_id):
        return traci.lane.getLastStepVehicleIDs(lane_id)

    def get_lane_veh_n(self, lane_id):
        return traci.lane.getLastStepVehicleNumber(lane_id)

    def get_lane_length(self, lane_id):
        return traci.lane.getLength(lane_id)

    def get_lane_veh_n_in_dist(self, lane_id, dist):
        return sum([1 for veh_id in self.get_lane_veh_ids(lane_id)
                    if (self.get_lane_length(lane_id) - self.get_veh_pos_on_lane(veh_id)) <= dist])

    def get_lane_veh_ids_in_dist(self, lane_id, dist):
        return [veh_id for veh_id in self.get_lane_veh_ids(lane_id)
                if (self.get_lane_length(lane_id) - self.get_veh_pos_on_lane(veh_id)) <= dist]

    def get_tl_lane_signals(self, tl_id):
        return [(l, s) for (l, s) in zip(
            [l[0][:-1] for l in traci.trafficlight.getControlledLinks(tl_id)],
            list(traci.trafficlight.getRedYellowGreenState(tl_id))
        )]

    def get_tl_lane_green(self, tl_id):
        return [list(set(t)) for t in zip(*[l for (l, s) in zip(
            [l[0][:-1] for l in traci.trafficlight.getControlledLinks(tl_id)],
            list(traci.trafficlight.getRedYellowGreenState(tl_id))
        ) if s.lower() == "g"])]

    def get_lane_edge_id(self, lane_id):
        return traci.lane.getEdgeID(lane_id)

    # edge

    def get_edge_veh_ids(self, edge_id):
        return traci.edge.getLastStepVehicleIDs(edge_id)

    def get_edge_lane_n(self, edge_id):
        return traci.edge.getLaneNumber(edge_id)

    # car

    def get_veh_type(self, veh_id):
        return traci.vehicle.getTypeID(veh_id)

    def get_veh_speed(self, veh_id):
        return traci.vehicle.getSpeed(veh_id)

    def get_veh_lane(self, veh_id):
        return traci.vehicle.getLaneID(veh_id)

    def get_veh_pos_on_lane(self, veh_id):
        return traci.vehicle.getLanePosition(veh_id)

    def get_veh_dist_from_junction(self, veh_id):
        return self.get_lane_length(self.get_veh_lane(veh_id)) - self.get_veh_pos_on_lane(veh_id)

    def get_veh_waiting_time(self, veh_id):
        return traci.vehicle.getWaitingTime(veh_id)

    def get_veh_accumulated_waiting_time(self, veh_id):
        return traci.vehicle.getAccumulatedWaitingTime(veh_id)

    def get_veh_delay(self, veh_id):
        return 1 - (self.get_veh_speed(veh_id) / self.args["v_max_speed"])

    ####################################################################################################################
    ####################################################################################################################

    # tl logic & signals

    def get_tl_edge_lanes(self, tl_id, edge_id):
        for edge in self.tl_net[tl_id]:
            for io in ["i", "o"]:
                if edge[io]["e"] == edge_id:
                    return edge[io]["l"]
        return []

    def get_tl_incoming_edges(self, tl_id):
        return [edge["i"]["e"] for edge in self.tl_net[tl_id]]

    def get_tl_outgoing_edges(self, tl_id):
        return [edge["o"]["e"] for edge in self.tl_net[tl_id]]

    def get_tl_incoming_lanes(self, tl_id):
        return [item for sublist in [edge["i"]["l"] for edge in self.tl_net[tl_id]] for item in sublist]

    def get_tl_outgoing_lanes(self, tl_id):
        return [item for sublist in [edge["o"]["l"] for edge in self.tl_net[tl_id]] for item in sublist]

    def get_all_incoming_edges(self):
        return [item for sublist in [self.get_tl_incoming_edges(tl_id) for tl_id in self.tl_ids] for item in sublist]

    def get_all_outgoing_edges(self):
        return [item for sublist in [self.get_tl_outgoing_edges(tl_id) for tl_id in self.tl_ids] for item in sublist]

    def get_all_incoming_lanes(self):
        return [item for sublist in [self.get_tl_incoming_lanes(tl_id) for tl_id in self.tl_ids] for item in sublist]

    def get_all_outgoing_lanes(self):
        return [item for sublist in [self.get_tl_outgoing_lanes(tl_id) for tl_id in self.tl_ids] for item in sublist]

    def gen_tl_net(self):
        return {tl_id: sorted([{
            "i": {"e": i, "l": [l.getID() for l in self.net.getEdge(i).getLanes()]},
            "o": {"e": o, "l": [l.getID() for l in self.net.getEdge(o).getLanes()]}
        } for (i, o) in zip(
            [i[1] for i in sorted([(i.getFromNode().getID(), i.getID()) for i in self.net.getNode(tl_id).getIncoming()])],
            [o[1] for o in sorted([(o.getToNode().getID(), o.getID()) for o in self.net.getNode(tl_id).getOutgoing()])]
        )], key=(lambda r: self.net.getEdge(r["o"]["e"]).getToNode().getCoord())) for tl_id in self.tl_ids}

    def get_next_yellow_phase_id(self, tl_id):
        return (self.get_phase(tl_id) + 1) % self.tl_logic[tl_id]["n"]

    def get_next_red_phase_id(self, tl_id):
        return (self.get_phase(tl_id) + 2) % self.tl_logic[tl_id]["n"]

    def get_next_green_phase_ryg_state(self, tl_id):
        return self.tl_logic[tl_id]["act"][
            (self.tl_logic[tl_id]["act"].index(self.get_ryg_state(tl_id)) + 1) % len(self.tl_logic[tl_id]["act"])
        ]

    def get_next_green_phase_id(self, tl_id):
        return self.get_new_green_phase_id(tl_id, self.get_next_green_phase_ryg_state(tl_id))

    def get_new_green_phase_id(self, tl_id, new_g):
        return self.tl_logic[tl_id]["map"][new_g]["id"]

    def get_red_tl_incoming_lanes(self, tl_id):
        try:
            r_li = [l for l in self.get_tl_incoming_lanes(tl_id) if
                    l not in self.tl_logic[tl_id]["map"][self.get_ryg_state(tl_id)]["li"]]
        except KeyError:
            r_li = []
        return r_li

    def get_red_tl_outgoing_lanes(self, tl_id):
        try:
            r_lo = [l for l in self.get_tl_outgoing_lanes(tl_id) if
                    l not in self.tl_logic[tl_id]["map"][self.get_ryg_state(tl_id)]["lo"]]
        except KeyError:
            r_lo = []
        return r_lo

    def get_green_tl_incoming_lanes(self, tl_id):
        try:
            g_li = [l for l in self.tl_logic[tl_id]["map"][self.get_ryg_state(tl_id)]["li"]]
        except KeyError:
            g_li = []
        return g_li

    def get_green_tl_outgoing_lanes(self, tl_id):
        try:
            g_lo = [l for l in self.tl_logic[tl_id]["map"][self.get_ryg_state(tl_id)]["lo"]]
        except KeyError:
            g_lo = []
        return g_lo

    def gen_tl_logic(self):
        tl_logic = {}
        for tl_id in self.tl_ids:
            tl_logic[tl_id] = {"n": 0, "act": [], "map": {}}
            for logic in traci.trafficlight.getAllProgramLogics(tl_id):
                if logic.programID == traci.trafficlight.getProgram(tl_id):
                    for p in range(len(logic.getPhases())):
                        traci.trafficlight.setPhase(tl_id, p)
                        s = traci.trafficlight.getRedYellowGreenState(tl_id)
                        if "g" in s.lower():
                            tl_logic[tl_id]["act"].append(s)
                            tl_logic[tl_id]["map"][s] = {k: v for (k, v) in zip(
                                ["li", "lo"], self.get_tl_lane_green(tl_id))}
                            tl_logic[tl_id]["map"][s]["id"] = p
                        tl_logic[tl_id]["n"] += 1

        return tl_logic

    def is_tl_lane_signal_green(self, tl_id, lane_id):
        return "g" in [list(self.get_ryg_state(tl_id))[i].lower() for i in self.tl_signals[tl_id][lane_id]]

    def gen_tl_signals(self):
        tl_signals = {tl_id: {} for tl_id in self.tl_ids}
        for tl_id in tl_signals:
            for (e, c) in enumerate(self.get_tl_lane_signals(tl_id)):
                if c[0][0] not in tl_signals[tl_id]:
                    tl_signals[tl_id][c[0][0]] = []
                tl_signals[tl_id][c[0][0]].append(e)

        return tl_signals

    ####################################################################################################################
    ####################################################################################################################

    # rou & flow logic

    def gen_route_net(self):
        return {"".join(r): r for r in [
            [e.getID() for e in self.net.getShortestPath(oe, de)[0]] for (oe, de) in [
                (self.net.getNode(on).getOutgoing()[0], self.net.getNode(dn).getIncoming()[0]) for (on, dn) in
                list(permutations([n for n in [node.getID() for node in self.net.getNodes()] if n not in self.tl_ids], 2))
                ]]}

    def gen_flow_logic(self):
        flow = {}

        for rou in self.route_net:
            if self.route_net[rou][0] not in flow:
                flow[self.route_net[rou][0]] = {"out": {}, "con": 0, "lam": 0., "pro": 0., "veh": 0}
            if self.route_net[rou][1] not in flow[self.route_net[rou][0]]["out"]:
                flow[self.route_net[rou][0]]["out"][self.route_net[rou][1]] = \
                    {"rou": [], "con": 0, "lam": 0., "pro": 0., "veh": 0}
            flow[self.route_net[rou][0]]["out"][self.route_net[rou][1]]["rou"].append(rou)

        con = {e: [] for e in flow}

        for l in self.get_all_incoming_lanes():
            e = self.net.getLane(l).getEdge().getID()
            if e in con:
                con[e].append([c.getToLane().getEdge().getID() for c in self.net.getLane(l).getOutgoing()])

        for e in con:
            c = [item for sublist in con[e] for item in sublist]
            c = dict(list(set([(o, c.count(o)) for o in c])))
            for o in sorted([o for o in c]):
                flow[e]["out"][o]["con"] = c[o]
                flow[e]["con"] += c[o]

        return flow

    def set_seed(self):
        if self.args["seed"]:
            random.seed(self.ep_count)
            np.random.seed(self.ep_count)

    def con_penetration_rate(self):
        self.ctrl_con_p_rate = random.randint(0, 1000) / 1000
        return self.ctrl_con_p_rate if self.rnd[0] else self.args["con_penetration_rate"]

    """
    def lambda_veh_p_second(self, veh_p_s):
        return 1 / veh_p_s
    """

    def lambda_veh_p_hour(self, veh_p_h):
        return 3600 / veh_p_h

    def insert_lambdas(self):
        lambdas = [self.lambda_veh_p_hour(random.randint(1, 10) * 100) for _ in self.flow_logic]
        return lambdas if self.rnd[1] else [self.lambda_veh_p_hour(f) for f in self.args["veh_p_hour"]]

    def update_flow_logic(self):
        self.set_seed()

        self.flow = []
        self.con_p_rate = self.con_penetration_rate()

        """"""
        lambdas = self.insert_lambdas()
        self.veh_n_p_hour = [3600 / l for l in lambdas]
        print("\n--- con:", self.con_p_rate, ", flow:", self.veh_n_p_hour, "---\n")
        """"""

        for i, e in enumerate(sorted([e for e in self.flow_logic])):
            self.flow_logic[e]["lam"] = lambdas[i]

            t, fi = 0, []
            while t < self.args["steps"]:
                fi.append(t)
                t += np.random.poisson(self.flow_logic[e]["lam"])

            self.flow_logic[e]["veh"] = len(fi)
            random.shuffle(fi)

            k = sorted([0., 1.] + [random.uniform(0, 1) for _ in range(self.flow_logic[e]["con"] - 1)])
            p = [a - b for a, b in zip(k[1:], k[:-1])]

            for o in self.flow_logic[e]["out"]:
                self.flow_logic[e]["out"][o]["pro"] = sum([p.pop() for _ in range(self.flow_logic[e]["out"][o]["con"])])
                self.flow_logic[e]["out"][o]["lam"] = self.flow_logic[e]["lam"] * self.flow_logic[e]["out"][o]["pro"]

                fo = [(fi.pop(), random.choice(self.flow_logic[e]["out"][o]["rou"]), False)
                      for _ in range(min([round(self.flow_logic[e]["veh"] * self.flow_logic[e]["out"][o]["pro"]), len(fi)]))]
                self.flow_logic[e]["out"][o]["veh"] = len(fo)

                self.flow += fo

            self.flow_logic[e]["veh"] = sum([self.flow_logic[e]["out"][o]["veh"] for o in self.flow_logic[e]["out"]])

        v = sum([self.flow_logic[e]["veh"] for e in self.flow_logic])
        for e in self.flow_logic:
            self.flow_logic[e]["pro"] = self.flow_logic[e]["veh"] / v

        for n in random.sample(list(range(v)), round(v * self.con_p_rate)):
            self.flow[n] = self.flow[n][:-1] + (True,)

        self.flow = sorted(self.flow)

    def generate_route_file(self, gen=True):
        with open(self.data_dir + self.config + ".rou.xml", "w") as f:
            print('<routes>', file=f)
            print('', file=f)

            print(f'    <vType id="{self.args["v_type_def"]}" accel="0.8" decel="4.5" sigma="0.5"' +
                  f' length="{self.args["v_length"]}" minGap="{self.args["v_min_gap"]}"' +
                  f' maxSpeed="{self.args["v_max_speed"]}" guiShape="passenger" />', file=f)
            print(f'    <vType id="{self.args["v_type_con"]}" accel="0.8" decel="4.5" sigma="0.5"' +
                  f' length="{self.args["v_length"]}" minGap="{self.args["v_min_gap"]}"' +
                  f' maxSpeed="{self.args["v_max_speed"]}" guiShape="passenger" />', file=f)
            print('', file=f)

            for rou in self.route_net:
                print(f'    <route id="{rou}" edges="{" ".join(self.route_net[rou])}" />', file=f)
            print('', file=f)

            if gen:
                self.veh_n = 0
                self.ep_count += 1
                self.update_flow_logic()
                for t, rou, co in self.flow:
                    self.veh_n += 1
                    v_type = self.args["v_type_con"] if co else self.args["v_type_def"]
                    print(f'    <vehicle id="{rou}_{self.veh_n}" type="{v_type}" route="{rou}" depart="{t}" />', file=f)
                print('', file=f)

            print('</routes>', file=f)

    ####################################################################################################################
    ####################################################################################################################

    # Connected vehicles

    def is_veh_con(self, veh_id):
        return self.get_veh_type(veh_id) == self.args["v_type_con"]

    ####################################################################################################################
    ####################################################################################################################

    # Log info

    def log_info(self):
        veh_n = 0
        sum_delay, sum_waiting_time, sum_queue_length, sum_acc_waiting_time = 0, 0, 0, 0

        for tl_id in self.tl_ids:
            for veh_id in self.yield_tl_vehs(tl_id):
                veh_n += 1
                sum_delay += self.get_veh_delay(veh_id)
                wt = self.get_veh_waiting_time(veh_id)
                sum_waiting_time += wt
                sum_acc_waiting_time += self.get_veh_accumulated_waiting_time(veh_id)
                if wt > 0:
                    sum_queue_length += 1

        avg_delay = 0 if veh_n == 0 else sum_delay / veh_n
        avg_waiting_time = 0 if veh_n == 0 else sum_waiting_time / veh_n
        avg_acc_waiting_time = 0 if veh_n == 0 else sum_acc_waiting_time / veh_n
        avg_queue_length = sum_queue_length / len(self.get_all_incoming_lanes())

        return {
            "id": type(self).__name__.lower(),
            "ep": self.ep_count,
            "con_p_rate": self.con_p_rate,
            "ctrl_con_p_rate": self.ctrl_con_p_rate,
            "veh_n_p_hour": json.dumps(self.veh_n_p_hour),
            "veh_n": veh_n,
            "sum_delay": sum_delay,
            "sum_waiting_time": sum_waiting_time,
            "sum_acc_waiting_time": sum_acc_waiting_time,
            "sum_queue_length": sum_queue_length,
            "avg_delay": avg_delay,
            "avg_waiting_time": avg_waiting_time,
            "avg_acc_waiting_time": avg_acc_waiting_time,
            "avg_queue_length": avg_queue_length
        }
