class TlScheduler:
    def __init__(self, tp_min, tl_ids):
        self.idx = 0
        self.size = tp_min + 1
        self.buffer = [[] for _ in range(self.size)]
        [self.push(0, (tl_id, None)) for tl_id in tl_ids]

    def push(self, t_evt, tl_evt):
        self.buffer[(self.idx + t_evt) % self.size].append(tl_evt)

    def pop(self):
        try:
            tl_evt = self.buffer[self.idx].pop(0)
        except IndexError:
            tl_evt = None
            self.idx = (self.idx + 1) % self.size
        return tl_evt
