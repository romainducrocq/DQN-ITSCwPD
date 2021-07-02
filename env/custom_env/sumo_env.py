# https://sumo.dlr.de/pydoc/

from __future__ import absolute_import, print_function

from .utils import \
    SUMO_PARAMS, \
    pretty_print

import sys
import random
import numpy as np
from itertools import permutations

SUMO_HOME = "./venv/sumo/"

sys.path.append(SUMO_HOME + 'tools')

from sumolib import net  # noqa
import traci  # noqa


class SumoEnv:
    SUMO_ENV = "./env/custom_env/"

    def __init__(self, gui=False):
        self.args = SUMO_PARAMS

        self.gui = False
        self.config = self.args["config"]
        self.data_dir = self.SUMO_ENV + "data/" + self.config + "/"

        self.net = net.readNet(self.data_dir + self.config + ".net.xml")
        self.tl_ids = [tl.getID() for tl in self.net.getTrafficLights()]

        self.tl_net = self.gen_tl_net()
        """
        pretty_print(self.tl_net)
        exit()
        """

        self.route_net = self.gen_route_net()
        self.flow_log = self.gen_flow_logic()
        self.flow = []
        """
        pretty_print(self.route_net)
        pretty_print(self.flow_log)
        exit()
        """

        self.update_flow_logic()
        """"""
        pretty_print(self.flow_log)
        # [print(f) for f in self.flow]
        exit()
        """"""

        _ = self.generate_route_file(gen=False)
        traci.start(self.set_params())

        self.tl_logic = self.gen_tl_logic()
        """
        pretty_print(self.tl_logic)
        exit()
        """

        self.gui = gui
        self.veh_n = 0
        self.steps = self.args["steps"]
        self.veh_ph = self.args["veh_ph"]

        self.params = self.set_params()

    def set_params(self):
        params = [
            SUMO_HOME + "bin/sumo" + ("-gui" if self.gui else ""), "-c",
            self.data_dir + self.config + ".sumocfg",
            "--tripinfo-output", self.data_dir + "tripinfo.xml"
        ]

        if self.gui:
            params += [
                "--delay", str(self.args["delay"]),
                "--start", "true", "--quit-on-end", "true",
                "--gui-settings-file", self.SUMO_ENV + "data/" + self.config + "/gui-settings.cfg"
            ]

        return params

    def start(self):
        self.veh_n = self.generate_route_file()
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
        raise NotImplementedError

    def is_simulation_end(self):
        return traci.simulation.getMinExpectedNumber() == 0

    def get_current_time(self):
        return traci.simulation.getCurrentTime() // 1000

    # traffic light

    def get_phase(self, tl_id):
        return traci.trafficlight.getPhase(tl_id)

    def get_ryg_state(self, tl_id):
        return traci.trafficlight.getRedYellowGreenState(tl_id)

    def set_phase(self, tl_id, phase):
        traci.trafficlight.setPhase(tl_id, phase)

    def set_phase_duration(self, tl_id, dur):
        traci.trafficlight.setPhaseDuration(tl_id, dur)

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

    def get_tl_lane_green(self, tl_id):
        return [list(set(t)) for t in zip(*[l for (l, s) in zip(
            [l[0][:-1] for l in traci.trafficlight.getControlledLinks(tl_id)],
            list(traci.trafficlight.getRedYellowGreenState(tl_id))
        ) if s.lower() == "g"])]

    # induction loop

    # car

    def get_veh_pos_on_lane(self, veh_id):
        return traci.vehicle.getLanePosition(veh_id)

    # maps & generators

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
        return {tl_id: [{
            "i": {"e": i, "l": [l.getID() for l in self.net.getEdge(i).getLanes()]},
            "o": {"e": o, "l": [l.getID() for l in self.net.getEdge(o).getLanes()]}
        } for (i, o) in zip(
            [i[1] for i in sorted([(i.getFromNode().getID(), i.getID()) for i in self.net.getNode(tl_id).getIncoming()])],
            [o[1] for o in sorted([(o.getToNode().getID(), o.getID()) for o in self.net.getNode(tl_id).getOutgoing()])]
        )] for tl_id in self.tl_ids}

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

    def update_flow_logic(self):
        self.flow = []

        lambdas = [(1 / random.uniform(0.1, 0.2)) for _ in self.flow_log]

        for i, e in enumerate(sorted([e for e in self.flow_log])):
            self.flow_log[e]["lam"] = lambdas[i]

            t, fi = 0, []
            while t < self.args["steps"]:
                fi.append(t)
                t += np.random.poisson(self.flow_log[e]["lam"])

            self.flow_log[e]["veh"] = len(fi)
            random.shuffle(fi)

            k = sorted([0., 1.] + [random.uniform(0, 1) for _ in range(self.flow_log[e]["con"] - 1)])
            p = [a - b for a, b in zip(k[1:], k[:-1])]

            for o in self.flow_log[e]["out"]:
                self.flow_log[e]["out"][o]["pro"] = sum([p.pop() for _ in range(self.flow_log[e]["out"][o]["con"])])
                self.flow_log[e]["out"][o]["lam"] = self.flow_log[e]["lam"] * self.flow_log[e]["out"][o]["pro"]

                fo = [(fi.pop(), random.choice(self.flow_log[e]["out"][o]["rou"]), False)
                      for _ in range(min([round(self.flow_log[e]["veh"] * self.flow_log[e]["out"][o]["pro"]), len(fi)]))]
                self.flow_log[e]["out"][o]["veh"] = len(fo)

                self.flow += fo

            self.flow_log[e]["veh"] = sum([self.flow_log[e]["out"][o]["veh"] for o in self.flow_log[e]["out"]])

        v = sum([self.flow_log[e]["veh"] for e in self.flow_log])
        for e in self.flow_log:
            self.flow_log[e]["pro"] = self.flow_log[e]["veh"] / v

        for n in random.sample(list(range(v)), round(v * self.args["veh_co_p"])):
            self.flow[n] = self.flow[n][:-1] + (True,)

        self.flow = sorted(self.flow)

    # flow & rou

    def poisson_flow(self, l):
        t, f = 0, []
        while t < self.steps:
            f.append(t)
            t += np.random.poisson(l)

        return f

    def get_flow_dist(self):
        return list(zip(
            sorted([random.uniform(0, 1) * 100 for _ in range(len(self.o_route_map) - 1)] + [100.]),
            [o for o in self.o_route_map]
        ))

    def get_o_dist(self, flow_dist):
        p = random.uniform(0, 1) * 100
        for f, o in flow_dist:
            if p <= f:
                return o

    def get_rou_dist(self, o=None):
        if o is None:
            o = random.choice([o for o in self.o_route_map])
        return random.choice(random.choice(self.o_route_map[o]))

    def get_flow_l(self):
        return 3600 / self.veh_ph

    def gen_rou_flow(self):
        flow_dist = self.get_flow_dist()
        for t in self.poisson_flow(self.get_flow_l()):
            yield t, self.get_rou_dist(o=self.get_o_dist(flow_dist))

    def generate_route_file(self, gen=True):
        with open(self.data_dir + self.config + ".rou.xml", "w") as f:
            print('<routes>', file=f)
            print('', file=f)

            print('    <vType id="veh" accel="0.8" decel="4.5" sigma="0.5" length="5" minGap="2.5" maxSpeed="16.67" guiShape="passenger" />', file=f)
            print('', file=f)

            for rou in self.route_net:
                print(f'    <route id="{rou}" edges="{" ".join(self.route_net[rou])}" />', file=f)
            print('', file=f)

            veh_n = 0
            if gen:
                for t, rou in self.gen_rou_flow():
                    # rou = random.choice([r for r in self.route_net])
                    print(f'    <vehicle id="{rou}_{veh_n}" type="veh" route="{rou}" depart="{t}" />', file=f)
                    veh_n += 1
                print('', file=f)

            print('</routes>', file=f)

            return veh_n
