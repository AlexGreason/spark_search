import golly as g
from collections import deque

direction = g.getstring("Enter direction (S or SE):", "S").upper()

if direction not in ["S", "SE"]:
    g.exit("Invalid direction")

delay = int(g.getstring("Enter delay:", "0"))
increase = int(g.getstring("Enter cell increase at penultimate step:", "1"))
offset = int(g.getstring("Enter horizontal offset between before/after:", "40"))
finalpop = int(g.getstring("Enter final population (-1 == don't care):", "-1"))
filename = g.getstring("Enter gencols filename:", "3g")
symm = g.getstring("Enter symmetries (x, d or xd):", "default")

if symm == "default":
    symm = ""
    if filename == "3g":
        symm += "x"
    if direction == "SE" and filename in ["2g", "3g", "s2g"]:
        symm += "d"

status = "dir: %s; delay %d; inc %d; symm %s; " % (direction, delay, increase, symm)
if finalpop >= 0: status += "finalpop %d; " % finalpop
status += "cols %s; " % filename

g.getevent()

[a, b] = [1, 1000] if direction == "S" else [1000, 1001]
    
cells = g.getcells(g.getrect())
cells = zip(cells[::3], cells[1::3], cells[2::3])

mx = -9999999
ox = oy = 0

for x, y, z in cells:
    if z != 3:
        continue
    idx = a * x + b * y
    if idx > mx:
        mx = idx
        ox = x
        oy = y

on_cells = []
off_cells = []
example_cells = []
start_cells = []

for x, y, z in cells:
    if x <= ox + offset // 2:
        if z == 3:
            example_cells.append(x - ox)
            example_cells.append(y - oy)
        elif z == 1:
            start_cells.append(x - ox)
            start_cells.append(y - oy)
    else:
        if z == 1:
            on_cells.append((x - ox - offset, y - oy))
        elif z == 2:
            off_cells.append((x - ox - offset, y - oy))


results_layer = g.addlayer()
g.setname("Results")
g.setrule("Life")
g.setalgo("QuickLife")
work_layer = g.addlayer()
g.setname("Work area")

g.putcells(start_cells)
g.putcells(example_cells)
g.run(delay)

if not all(g.getcell(x, y) for x, y in on_cells) or any(g.getcell(x, y) for x, y in off_cells):
    g.warn("Warning: the example pattern is not a solution")

results = 0

def apply_sym(pat, symm):
    yield pat
    if "x" in symm: yield g.transform(pat, 0, 0, -1, 0, 0, 1)
    if "d" in symm: yield g.transform(pat, 0, 0,  0, 1, 1, 0)
    if "x" in symm and "d" in symm:
        yield g.transform(pat, 0, 0, 1, -1, 0)

def testkey():
    if results and g.getevent().startswith("key x"):
        g.setlayer(results_layer)
        g.select(g.getrect())
        g.copy()
        g.select([])
        g.setlayer(work_layer)
        
def test(pat, gen, loc, x, y):

    global results
    
    if not all(g.getcell(x+loc, y) for x, y in on_cells):
        return
    
    if any(g.getcell(x+loc, y) for x, y in off_cells):
        return

    begin = start_cells + g.evolve(g.transform(pat, -x, -y), gen)

    if finalpop >= 0 and len(g.evolve(begin, 100)) != 2 * finalpop:
        return

    results += 1
    g.setlayer(results_layer)
    g.putcells(g.evolve(pat, gen % 8), 50 * results-x, -y)
    g.putcells(begin, 50 * results, 50)
    g.putcells(g.evolve(begin, delay), 50 * results, 100)
    g.setlayer(work_layer)

    
count = 0
for s in open("gencols/" + filename + ".col"):
    count += 1
    pat = g.parse(s.split(" ")[0].replace('!','$').replace('.','b').replace('*','o')+'!')
    if count % 100 == 0:
        g.show(status + "results %d; <x> to copy to clipboard. count %d" % (results, count))
        testkey()

    for pat in apply_sym(pat, symm):
        g.new('')
        g.putcells(pat)
        q = deque()
        orect = [-128, -128, 256, 256]
        all_max = -9999999
        locs = set()
        for gen in range(80 + delay):

            cells = g.getcells(orect)
            current_max = -9999999
            for i in range(0, len(cells), 2):
                idx = a * cells[i] + b * cells[i+1]
                if idx > current_max:
                    current_max = idx
                    ox = cells[i]
                    oy = cells[i+1]

            if gen > 0 and current_max >= all_max + increase:
                loc = 256
                while loc in locs:
                    loc += 256
                locs.add(loc)
                q.append((gen, loc, ox, oy))
                g.putcells(cells, loc - ox, -oy)
                g.putcells(start_cells, loc)

            if q and q[0][0] + delay == gen:
                test(pat, *q[0])
                g.select([-128 + q[0][1], -128, 256, 256])
                g.clear(0)
                locs.remove(q[0][1])
                q.popleft()
            
            all_max = max(all_max, current_max)
            g.run(1)

testkey()
g.dellayer()
g.setlayer(results_layer)
g.fit()
