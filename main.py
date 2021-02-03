

"""Find optimal musical scale. Exponential but not far from just intonation."""


import math
import sys


class ComputingPoint:
    def __init__(
        self,
        cotone,
        val_lo=0.0,
        iteration=2,
        prev_cpoint=None,
        next_cpoint=None,
        prev_mpoint=None,
        next_mpoint=None,
    ):
        self.cotone = cotone
        self.val_lo = val_lo
        self.iteration = iteration
        self.prev_cpoint = prev_cpoint
        self.next_cpoint = next_cpoint
        self.prev_mpoint = prev_mpoint
        self.next_mpoint = next_mpoint

    @property
    def val_hi(self):
        return self.val_lo + 1.0 / (self.iteration + 1)

    def bump(self):
        self.iteration += 1
        coeff = 1.0 / self.iteration - 1.0 / (self.iteration + 1)
        weights = list()
        intervals = list()
        for subiter in range(1, self.iteration):
            counteriter = self.iteration - subiter
            if counteriter <= subiter:
                break
            intervals.append(counteriter / subiter)
            weights.append(subiter)
        coeff /= sum(weights)
        for index, weight in enumerate(weights):
            sinn = math.sin(self.cotone * math.log(intervals[index]))
            self.val_lo += coeff * weight * sinn * sinn
        return self


class MidPoint:
    def __init__(
        self,
        prev_cpoint=None,
        next_cpoint=None,
        cotone=None,
        slope=None,
    ):
        self.prev_cpoint = prev_cpoint
        self.next_cpoint = next_cpoint
        self.cotone = None
        self.slope = None

    def bump(self, min_val):
        prev_hi = self.prev_cpoint.val_hi
        next_hi = self.next_cpoint.val_hi
        prev_co = self.prev_cpoint.cotone
        next_co = self.next_cpoint.cotone
        abs_prev_hi = abs(prev_hi - min_val)
        self.slope = (abs_prev_hi + abs(next_hi - min_val)) / abs(next_co - prev_co)
        self.cotone = prev_co + abs_prev_hi / self.slope
#        print(f"mpoint bump debug: prev_hi {prev_hi} next_hi {next_hi} prev_co {prev_co} next_co {next_co} slope {self.slope} cotone {self.cotone}")
        return self

def main():
    classic = ComputingPoint(cotone=math.pi*12/math.log(2.0))
    print(f"classic cotone={classic.cotone}")
#    sys.exit(0)
    cpoints = list()
    mpoints = list()
    # 12.0 is the classic. {12.01226522952678, 12.012322435401824}
    first = ComputingPoint(cotone=math.pi*11.0 / math.log(2.0)).bump()
#    first = ComputingPoint(cotone=math.pi*30.9690 / math.log(2.0)).bump()
    cpoints.append(first)
    # ~41.0 is next better. {40.99026553761196, 40.99042247831756}
    last = ComputingPoint(cotone=math.pi*40.0 / math.log(2.0)).bump()
#    last = ComputingPoint(cotone=math.pi*30.9695 / math.log(2.0)).bump()
    # ~31 is to be found, it is better than the known ~19. {18.952311277376694, 18.95282021060691}
    # It is somewhere around {30.969307519580894, 30.969306649168946}.
    cpoints.append(last)
    min_val = min(first.val_lo, last.val_lo)
    mid = MidPoint(prev_cpoint=first, next_cpoint=last).bump(min_val=min_val)
    mpoints.append(mid)
    first.next_cpoint = last
    last.prev_cpoint = first
    first.next_mpoint = mid
    last.prev_mpoint = mid
    max_iter = first.iteration
    old_bumped_cotone = None
    old_max = 10.0
    old_iter = 0
    bumps = 0
    while 1:
        #cpoints.sort(key=lambda x: x.val_lo)
        best_index = None
        best_val = 10.0
        for index, point in enumerate(cpoints):
            val_lo = point.val_lo
            if val_lo < best_val:
                best_val = val_lo
                best_index = index
        cpoints[0], cpoints[best_index] = cpoints[best_index], cpoints[0]
        new_bumped_cpoint = cpoints[0]
#        print(f"Debug bumping cpoint at cotone {new_bumped_cpoint.cotone}; old_min: {new_bumped_cpoint.val_lo}, old_max: {new_bumped_cpoint.val_hi}")
        new_bumped_cpoint.bump()
#        print(f"Debug new_min: {new_bumped_cpoint.val_lo}, new_max: {new_bumped_cpoint.val_hi}")
        new_min = new_bumped_cpoint.val_lo
        if new_bumped_cpoint.prev_mpoint is not None:
            new_bumped_cpoint.prev_mpoint.bump(min_val=new_min)
        if new_bumped_cpoint.next_mpoint is not None:
            new_bumped_cpoint.next_mpoint.bump(min_val=new_min)
        new_max = new_bumped_cpoint.val_hi
        if new_max < old_max:
            print(f"New max: cotone={new_bumped_cpoint.cotone}, iteration={new_bumped_cpoint.iteration}, min={new_min}, max={new_max}", flush=True)
            print(f"tones per octave: {new_bumped_cpoint.cotone * math.log(2.0) / math.pi}", flush=True)
            old_max = new_max
        if new_bumped_cpoint.iteration <= old_iter:
            bumps += 1
            continue
        old_iter = new_bumped_cpoint.iteration
#        if new_bumped_cpoint.cotone != old_bumped_cotone:
##            print(f"Debug best cpoint changed, not bisecting.")
#            old_bumped_cotone = new_bumped_cpoint.cotone
#            continue
        #mpoints.sort(key=lambda x: x.slope)
        best_index = None
        best_slope = 1e100
        for index, point in enumerate(mpoints):
            slope = point.slope
            if slope < best_slope:
                best_slope = slope
                best_index = index
        mpoints[0], mpoints[best_index] = mpoints[best_index], mpoints[0]
        chosen = mpoints[0]
        print(f"Choosing to upgrade previous midpoint at cotone={chosen.cotone}, slope={chosen.slope}; max slope at cotone={mpoints[-1].cotone}, slope={mpoints[-1].slope}", flush=True)
        prev_slope = None if new_bumped_cpoint.prev_mpoint is None else new_bumped_cpoint.prev_mpoint.slope
        next_slope = None if new_bumped_cpoint.next_mpoint is None else new_bumped_cpoint.next_mpoint.slope
        print(f"Cpoint bumps since last print: {bumps}. Slopes near best; prev={prev_slope}, next={next_slope}", flush=True)
        bumps = 0
        #mpoints = mpoints[1:]
        new_cpoint = ComputingPoint(cotone=chosen.cotone, prev_cpoint=chosen.prev_cpoint, next_cpoint=chosen.next_cpoint).bump()
        cpoints.append(new_cpoint)
        prev_mpoint = MidPoint(prev_cpoint=chosen.prev_cpoint, next_cpoint=new_cpoint).bump(min_val=new_min)
        #mpoints.append(prev_mpoint)
        mpoints[0] = prev_mpoint
        next_mpoint = MidPoint(prev_cpoint=new_cpoint, next_cpoint=chosen.next_cpoint).bump(min_val=new_min)
        mpoints.append(next_mpoint)
        chosen.prev_cpoint.next_mpoint = prev_mpoint
        chosen.prev_cpoint.next_cpoint = new_cpoint
        new_cpoint.prev_mpoint = prev_mpoint
        new_cpoint.next_mpoint = next_mpoint
        chosen.next_cpoint.prev_cpoint = new_cpoint
        chosen.next_cpoint.prev_mpoint = next_mpoint
        # continue

main()
