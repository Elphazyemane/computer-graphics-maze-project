import pygame
import sys
import random

#  CONFIGURATION
ROWS      = 15
COLS      = 20
CELL_SIZE = 40

WIDTH  = COLS * CELL_SIZE
HEIGHT = ROWS * CELL_SIZE

# Animation delays (milliseconds per frame)
GEN_DELAY   = 18
SOLVE_DELAY = 25

# Colors
C_BG          = (18,  18,  28)
C_WALL        = (220, 220, 240)
C_MOUSE_GEN   = (100, 220, 100)
C_VISITED_GEN = (40,  60,  80)
C_PATH        = (255,  80,  80)
C_DEAD        = (60,  100, 180)
C_TREE_NODE   = (255, 200,  50)
C_TREE_EDGE   = (255, 200,  50)
C_START       = (50,  230, 120)
C_END         = (255, 120,  50)


def make_walls():
    north = [[True] * (COLS + 1) for _ in range(ROWS + 1)]
    east  = [[True] * (COLS + 2) for _ in range(ROWS + 1)]
    return north, east


#  COORDINATE HELPERS
def cell_top_left(r, c):
    """Pixel (x, y) of the top-left corner of cell (r, c)."""
    x = (c - 1) * CELL_SIZE
    y = (ROWS - r) * CELL_SIZE
    return x, y

def cell_center(r, c):
    x, y = cell_top_left(r, c)
    return x + CELL_SIZE // 2, y + CELL_SIZE // 2


#  DRAWING UTILITIES
def draw_cell_bg(screen, r, c, color):
    x, y = cell_top_left(r, c)
    pygame.draw.rect(screen, color,
                     (x + 1, y + 1, CELL_SIZE - 1, CELL_SIZE - 1))

def draw_dot(screen, r, c, color, radius=7):
    pygame.draw.circle(screen, color, cell_center(r, c), radius)

def draw_walls(screen, northWall, eastWall):
    """Draw every intact wall."""
    for r in range(1, ROWS + 1):
        for c in range(1, COLS + 1):
            x, y = cell_top_left(r, c)
            if northWall[r][c]:
                pygame.draw.line(screen, C_WALL,
                                 (x,             y),
                                 (x + CELL_SIZE, y), 2)
            if eastWall[r][c]:
                pygame.draw.line(screen, C_WALL,
                                 (x + CELL_SIZE, y),
                                 (x + CELL_SIZE, y + CELL_SIZE), 2)

    # South border (phantom row 0)
    for c in range(1, COLS + 1):
        x, y = cell_top_left(1, c)
        if northWall[0][c]:
            pygame.draw.line(screen, C_WALL,
                             (x,             y + CELL_SIZE),
                             (x + CELL_SIZE, y + CELL_SIZE), 2)

    # West border (phantom col 0)
    for r in range(1, ROWS + 1):
        x, y = cell_top_left(r, 1)
        if eastWall[r][0]:
            pygame.draw.line(screen, C_WALL,
                             (x, y),
                             (x, y + CELL_SIZE), 2)

def draw_tree(screen, tree_edges):
    """Draw the spanning-tree overlay (edges then nodes)."""
    for (r1, c1), (r2, c2) in tree_edges:
        pygame.draw.line(screen, C_TREE_EDGE,
                         cell_center(r1, c1),
                         cell_center(r2, c2), 2)
    drawn = set()
    for (r1, c1), (r2, c2) in tree_edges:
        for cell in ((r1, c1), (r2, c2)):
            if cell not in drawn:
                pygame.draw.circle(screen, C_TREE_NODE,
                                   cell_center(*cell), 4)
                drawn.add(cell)

def draw_start_end(screen, start, end):
    for cell, color in ((start, C_START), (end, C_END)):
        r, c = cell
        x, y = cell_top_left(r, c)
        pygame.draw.rect(screen, color,
                         (x + 2, y + 2, CELL_SIZE - 3, CELL_SIZE - 3), 3)


#  WALL REMOVAL HELPER
def remove_wall_between(northWall, eastWall, r1, c1, r2, c2):
    """Knock down the shared wall between adjacent cells (r1,c1) and (r2,c2)."""
    if r2 == r1 + 1:            # (r2,c2) is above
        northWall[r1][c1] = False
    elif r2 == r1 - 1:          # (r2,c2) is below
        northWall[r2][c2] = False
    elif c2 == c1 + 1:          # (r2,c2) is to the right
        eastWall[r1][c1] = False
    elif c2 == c1 - 1:          # (r2,c2) is to the left
        eastWall[r1][c2] = False


#  MAZE GENERATION  
def generate_maze(screen, clock):
   
    northWall, eastWall = make_walls()
    tree_edges = []   # list of ((r1,c1),(r2,c2)) — the spanning tree
    visited = [[False] * (COLS + 1) for _ in range(ROWS + 1)]

    sr, sc = random.randint(1, ROWS), random.randint(1, COLS)
    visited[sr][sc] = True
    stack = [(sr, sc)]

    def neighbours(r, c):
        nb = []
        if r < ROWS: nb.append((r + 1, c))
        if r > 1:    nb.append((r - 1, c))
        if c < COLS: nb.append((r, c + 1))
        if c > 1:    nb.append((r, c - 1))
        return nb

    while stack:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

        r, c = stack[-1]
        unvisited = [(nr, nc) for nr, nc in neighbours(r, c)
                     if not visited[nr][nc]]

        if unvisited:
            nr, nc = random.choice(unvisited)
            remove_wall_between(northWall, eastWall, r, c, nr, nc)
            tree_edges.append(((r, c), (nr, nc)))
            visited[nr][nc] = True
            stack.append((nr, nc))
        else:
            stack.pop()

        #  animate 
        screen.fill(C_BG)
        for vr in range(1, ROWS + 1):
            for vc in range(1, COLS + 1):
                if visited[vr][vc]:
                    draw_cell_bg(screen, vr, vc, C_VISITED_GEN)
        draw_walls(screen, northWall, eastWall)
        if stack:
            draw_dot(screen, stack[-1][0], stack[-1][1], C_MOUSE_GEN, 8)
        pygame.display.flip()
        clock.tick(1000 // GEN_DELAY)

    #  entry and exit openings
    start = (random.randint(1, ROWS), 1)
    end   = (random.randint(1, ROWS), COLS)
    eastWall[start[0]][0]    = False   # gap in west border
    eastWall[end[0]][end[1]] = False   # gap in east border

    # Final static frame
    screen.fill(C_BG)
    draw_walls(screen, northWall, eastWall)
    draw_start_end(screen, start, end)
    pygame.display.flip()

    return northWall, eastWall, tree_edges, start, end


#  MAZE SOLVER  
def can_move(northWall, eastWall, r, c, direction):
    """True if movement in `direction` from (r,c) is not blocked by a wall."""
    if direction == 'N': return r < ROWS and not northWall[r][c]
    if direction == 'S': return r > 1    and not northWall[r - 1][c]
    if direction == 'E': return c < COLS and not eastWall[r][c]
    if direction == 'W': return c > 1    and not eastWall[r][c - 1]
    return False

def step(r, c, direction):
    if direction == 'N': return r + 1, c
    if direction == 'S': return r - 1, c
    if direction == 'E': return r,     c + 1
    if direction == 'W': return r,     c - 1


def solve_maze(screen, clock, northWall, eastWall,
               tree_edges, start, end, show_tree):
    
    visited = [[False] * (COLS + 1) for _ in range(ROWS + 1)]
    path    = [start]
    dead    = set()
    visited[start[0]][start[1]] = True
    DIRS = ['N', 'S', 'E', 'W']

    def redraw():
        screen.fill(C_BG)
        if show_tree[0]:
            draw_tree(screen, tree_edges)
        for dr, dc in dead:
            draw_cell_bg(screen, dr, dc, (25, 45, 95))
        for pr, pc in path:
            draw_cell_bg(screen, pr, pc, (80, 20, 20))
        draw_walls(screen, northWall, eastWall)
        draw_start_end(screen, start, end)
        for dr, dc in dead:
            draw_dot(screen, dr, dc, C_DEAD, 5)
        for pr, pc in path:
            draw_dot(screen, pr, pc, C_PATH, 7)
        if path:
            draw_dot(screen, path[-1][0], path[-1][1], (255, 255, 255), 4)
        pygame.display.flip()

    solved = False
    while path and not solved:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_t:
                show_tree[0] = not show_tree[0]

        r, c = path[-1]
        if (r, c) == end:
            solved = True
            break

        dirs = DIRS[:]
        random.shuffle(dirs)
        moved = False
        for d in dirs:
            nr, nc = step(r, c, d)
            if can_move(northWall, eastWall, r, c, d) and not visited[nr][nc]:
                visited[nr][nc] = True
                path.append((nr, nc))
                moved = True
                break

        if not moved:
            dead.add(path.pop())

        redraw()
        clock.tick(1000 // SOLVE_DELAY)

    redraw()

    #  victory flash 
    for _ in range(3):
        for pr, pc in path:
            draw_dot(screen, pr, pc, (255, 255, 100), 7)
        pygame.display.flip()
        pygame.time.wait(180)
        redraw()
        pygame.time.wait(180)


#  HUD
HUD_H = 24

HINTS = {
    'idle':      "SPACE = generate maze",
    'generated': "ENTER = solve   |   T = tree overlay   |   SPACE = new maze",
    'solved':    "SPACE = new maze   |   T = tree overlay",
}

def draw_hud(screen, font, state):
    pygame.draw.rect(screen, (10, 10, 20),
                     (0, HEIGHT, WIDTH, HUD_H))
    surf = font.render(HINTS.get(state, ""), True, (150, 150, 200))
    screen.blit(surf, (8, HEIGHT + (HUD_H - surf.get_height()) // 2))
    pygame.display.update(pygame.Rect(0, HEIGHT, WIDTH, HUD_H))


#  MAIN LOOP
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT + HUD_H))
    pygame.display.set_caption("Maze Generator & Solver")
    clock = pygame.time.Clock()
    font  = pygame.font.SysFont("monospace", 13)

    northWall = eastWall = tree_edges = start = end = None
    show_tree = [False]
    state = 'idle'

    screen.fill(C_BG)
    draw_hud(screen, font, state)
    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN:

                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    pygame.quit(); sys.exit()

                # Generate a new maze
                if event.key == pygame.K_SPACE:
                    show_tree[0] = False
                    northWall, eastWall, tree_edges, start, end = \
                        generate_maze(screen, clock)
                    state = 'generated'
                    draw_hud(screen, font, state)

                # Solve the current maze
                if event.key == pygame.K_RETURN and state == 'generated':
                    solve_maze(screen, clock,
                               northWall, eastWall, tree_edges,
                               start, end, show_tree)
                    state = 'solved'
                    draw_hud(screen, font, state)

                # Toggle spanning-tree overlay
                if event.key == pygame.K_t and state in ('generated', 'solved'):
                    show_tree[0] = not show_tree[0]
                    screen.fill(C_BG)
                    if show_tree[0]:
                        draw_tree(screen, tree_edges)
                    draw_walls(screen, northWall, eastWall)
                    draw_start_end(screen, start, end)
                    draw_hud(screen, font, state)
                    pygame.display.flip()

        clock.tick(30)


if __name__ == "__main__":
    main()