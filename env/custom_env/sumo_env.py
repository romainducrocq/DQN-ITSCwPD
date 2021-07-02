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
        self.gui = False
        self.config = SUMO_PARAMS["config"]
        self.data_dir = self.SUMO_ENV + "data/" + self.config + "/"

        self.net = net.readNet(self.data_dir + self.config + ".net.xml")
        self.tl_ids = [tl.getID() for tl in self.net.getTrafficLights()]

        self.tl_net = self.gen_tl_net()
        """
        pretty_print(self.tl_net)
        exit()
        """

        """
        self.con_net = self.gen_con_net()
        pretty_print(self.con_net)
        """

        self.route_net = self.gen_route_net()
        self.o_route_map = self.gen_o_route_map()
        """
        pretty_print(self.route_net)
        pretty_print(self.o_route_map)
        exit()
        """

        _ = self.generate_route_file(gen=False)
        traci.start(self.set_params())

        self.tl_logic = self.gen_tl_logic()
        """
        pretty_print(self.tl_logic)
        exit()
        """

        self.gui = gui
        self.veh_n = 0
        self.steps = SUMO_PARAMS["steps"]
        self.veh_ph = SUMO_PARAMS["veh_ph"]
        # self.tg = SUMO_PARAMS["tg"]
        # self.ty = SUMO_PARAMS["ty"]

        self.params = self.set_params()

    def set_params(self):
        params = [
            SUMO_HOME + "bin/sumo" + ("-gui" if self.gui else ""), "-c",
            self.data_dir + self.config + ".sumocfg",
            "--tripinfo-output", self.data_dir + "tripinfo.xml"
        ]

        if self.gui:
            params += [
                "--delay", str(SUMO_PARAMS["delay"]),
                "--start", "true", "--quit-on-end", "true",
                "--gui-settings-file", self.SUMO_ENV + "data/" + self.config + "/gui-settings.cfg"
            ]

        return params

    def start(self):
        self.veh_n = self.generate_route_file()
        traci.start(self.params)

    @staticmethod
    def stop():
        traci.close()
        sys.stdout.flush()

    def simulation_reset(self):
        SumoEnv.stop()
        self.start()

    @staticmethod
    def simulation_step():
        traci.simulationStep()

    def reset(self):
        raise NotImplementedError

    def step(self):
        raise NotImplementedError

    def obs(self):
        raise NotImplementedError

    def rew(self):
        raise NotImplementedError

    def done(self):
        raise NotImplementedError

    def info(self):
        raise NotImplementedError

    @staticmethod
    def is_simulation_end():
        return traci.simulation.getMinExpectedNumber() == 0

    @staticmethod
    def get_current_time():
        return traci.simulation.getCurrentTime() // 1000

    # traffic light

    """
    @staticmethod
    def set_tl_program(tl_id, program_id):
        traci.trafficlight.setProgram(tl_id, program_id)
    """

    @staticmethod
    def get_phase(tl_id):
        return traci.trafficlight.getPhase(tl_id)

    @staticmethod
    def get_ryg_state(tl_id):
        return traci.trafficlight.getRedYellowGreenState(tl_id)

    @staticmethod
    def set_phase(tl_id, phase):
        traci.trafficlight.setPhase(tl_id, phase)

    @staticmethod
    def set_phase_duration(tl_id, dur):
        traci.trafficlight.setPhaseDuration(tl_id, dur)

    # lane

    @staticmethod
    def get_lane_veh_ids(lane_id):
        return traci.lane.getLastStepVehicleIDs(lane_id)

    @staticmethod
    def get_lane_veh_n(lane_id):
        return traci.lane.getLastStepVehicleNumber(lane_id)

    @staticmethod
    def get_lane_length(lane_id):
        return traci.lane.getLength(lane_id)

    @staticmethod
    def get_lane_veh_n_in_dist(lane_id, dist):
        return sum([1 for veh_id in SumoEnv.get_lane_veh_ids(lane_id)
                    if (SumoEnv.get_lane_length(lane_id) - SumoEnv.get_veh_pos_on_lane(veh_id)) <= dist])

    @staticmethod
    def get_lane_veh_ids_in_dist(lane_id, dist):
        return [veh_id for veh_id in SumoEnv.get_lane_veh_ids(lane_id)
                if (SumoEnv.get_lane_length(lane_id) - SumoEnv.get_veh_pos_on_lane(veh_id)) <= dist]

    """
    @staticmethod
    def get_tl_lane_signals(tl_id):
        return [(l, s) for (l, s) in zip(
            [l[0][:-1] for l in traci.trafficlight.getControlledLinks(tl_id)],
            list(traci.trafficlight.getRedYellowGreenState(tl_id))
        )]
    """

    @staticmethod
    def get_tl_lane_green(tl_id):
        return [list(set(t)) for t in zip(*[l for (l, s) in zip(
            [l[0][:-1] for l in traci.trafficlight.getControlledLinks(tl_id)],
            list(traci.trafficlight.getRedYellowGreenState(tl_id))
        ) if s.lower() == "g"])]

    # induction loop

    """
    @staticmethod
    def get_induction_loop_last_step_vehicle_number(il_id):
        return traci.inductionloop.getLastStepVehicleNumber(il_id)
    """

    # edge

    """
    @staticmethod
    def get_cars_on_edge(edge_id):
        try:
            return traci.edge.getLastStepVehicleIDs(edge_id)
        except traci.exceptions.TraCIException as e:
            print(e)
            return None
    """

    # car

    """
    @staticmethod
    def get_car_speed(veh_id):
        return traci.vehicle.getSpeed(veh_id)

    @staticmethod
    def get_cars_relative_speed(veh_id1, veh_id2):
        return traci.vehicle.getSpeed(veh_id1) - traci.vehicle.getSpeed(veh_id2)
    """

    @staticmethod
    def get_veh_pos_on_lane(veh_id):
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

    """
    def gen_con_net(self):
        con = {l: [c.getToLane().getID() for c in self.net.getLane(l).getOutgoing()] for l in self.get_all_incoming_lanes()}
        
        
        # return {l: [c.getToLane().getID() for c in self.net.getLane(l).getOutgoing()] for l in self.get_all_incoming_lanes()}
    #         return {self.net.getLane(l).getEdge().getID(): [c.getToLane().getEdge().getID() for c in self.net.getLane(l).getOutgoing()] for l in self.get_all_incoming_lanes()}
    """

    def get_next_yellow_phase_id(self, tl_id):
        return (SumoEnv.get_phase(tl_id) + 1) % self.tl_logic[tl_id]["n"]

    def get_next_green_phase_ryg_state(self, tl_id):
        return self.tl_logic[tl_id]["act"][
            (self.tl_logic[tl_id]["act"].index(SumoEnv.get_ryg_state(tl_id)) + 1) % len(self.tl_logic[tl_id]["act"])
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
            g_li = [l for l in self.tl_logic[tl_id]["map"][SumoEnv.get_ryg_state(tl_id)]["li"]]
        except KeyError:
            g_li = []
        return g_li

    def get_green_tl_outgoing_lanes(self, tl_id):
        try:
            g_lo = [l for l in self.tl_logic[tl_id]["map"][SumoEnv.get_ryg_state(tl_id)]["lo"]]
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
                                ["li", "lo"], SumoEnv.get_tl_lane_green(tl_id))}
                            tl_logic[tl_id]["map"][s]["id"] = p
                        tl_logic[tl_id]["n"] += 1

        return tl_logic

    def gen_route_net(self):
        return {"".join(r): r for r in [
            [e.getID() for e in self.net.getShortestPath(oe, de)[0]] for (oe, de) in [
                (self.net.getNode(on).getOutgoing()[0], self.net.getNode(dn).getIncoming()[0]) for (on, dn) in
                list(permutations([n for n in [node.getID() for node in self.net.getNodes()] if n not in self.tl_ids], 2))
                ]]}

    def gen_o_route_map(self):
        o_con = {e: [] for e in list(set([self.route_net[rou][0] for rou in self.route_net]))}

        for l in self.get_all_incoming_lanes():
            e = self.net.getLane(l).getEdge().getID()
            if e in o_con:
                o_con[e].append([c.getToLane().getEdge().getID() for c in self.net.getLane(l).getOutgoing()])

        o_rou = {e: [[] for _ in range(len(o_con[e]))] for e in [e for e in o_con]}

        for rou in self.route_net:
            for e0 in o_con:
                for l in range(len(o_con[e0])):
                    for e1 in o_con[e0][l]:
                        if e0 == self.route_net[rou][0] and e1 == self.route_net[rou][1]:
                            o_rou[e0][l].append(rou)

        return o_rou

    # flow & rou

    """
    def flow_distribution(self):
        return 1. / 2

    def flow_uniform(self, p):
        return random.uniform(0, 1) < p
    """

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
