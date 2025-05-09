import pygame
import sys
import random
from enum import Enum
import numpy as np

# Initialize pygame
pygame.init()

# Constants
GRID_SIZE = 12
CELL_SIZE = 50
MARGIN = 50
WINDOW_WIDTH = GRID_SIZE * CELL_SIZE * 2 + MARGIN * 3
WINDOW_HEIGHT = GRID_SIZE * CELL_SIZE + MARGIN * 2 + 100  # Extra space for buttons

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
DARK_RED = (180, 0, 0)
LIGHT_GRAY = (230, 230, 230)
DARK_GRAY = (120, 120, 120)  # Darker gray for previously seen walls

# Direction enum
class Direction(Enum):
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3

class Founder:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.direction = random.choice(list(Direction))
        self.base_visibility = 1  # Base visibility without talking to users
        self.temporary_boost = 0  # Temporary visibility boost from talking to users
        self.max_visibility = 2   # Maximum visibility with boost
        
        # Load founder image
        self.original_image = pygame.image.load('alex.jpg')
        # Scale the image to fit within a cell (slightly smaller than cell size)
        self.founder_size = int(CELL_SIZE * 0.7)  # Make slightly smaller to fit with arrow
        self.image = pygame.transform.scale(self.original_image, (self.founder_size, self.founder_size))
        
        # Arrow properties
        self.arrow_length = int(CELL_SIZE * 0.4)
        self.arrow_width = 3
        self.arrow_head_size = 8
    
    @property
    def visibility(self):
        return min(self.base_visibility + self.temporary_boost, self.max_visibility)
    
    def pivot(self):
        # Choose a random direction other than the current one
        possible_directions = [d for d in Direction if d != self.direction]
        self.direction = random.choice(possible_directions)
    
    def build(self, maze):
        # Reset temporary visibility boost when building
        self.temporary_boost = 0
        
        new_x, new_y = self.x, self.y
        
        if self.direction == Direction.UP:
            new_y -= 1
        elif self.direction == Direction.RIGHT:
            new_x += 1
        elif self.direction == Direction.DOWN:
            new_y += 1
        elif self.direction == Direction.LEFT:
            new_x -= 1
        
        # Check if the new position is valid and not a wall
        if (0 <= new_x < GRID_SIZE and 0 <= new_y < GRID_SIZE and 
            maze[new_y][new_x] != 1):  # 1 represents wall
            self.x, self.y = new_x, new_y
    
    def talk_to_user(self):
        # Temporarily increase visibility by 1 (up to max_visibility)
        self.temporary_boost = 1

    def fundraise(self):
        # Does nothing as per requirements
        pass

class IdeaMaze:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("The Idea Maze")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 24)
        self.large_font = pygame.font.SysFont(None, 72)
        
        # Create the mazes
        self.debug_maze, self.player_maze, self.pmf_pos, self.founder_pos = self.generate_maze()
        
        # Create the founder
        self.founder = Founder(self.founder_pos[0], self.founder_pos[1])
        
        # Game state
        self.game_won = False
        self.game_over = False
        self.runway = 48  # Runway in months
        self.debug_mode = True  # Debug mode enabled by default
        
        # Keep track of which cells have been seen
        self.visited_cells = np.zeros((GRID_SIZE, GRID_SIZE), dtype=bool)
        # Mark cells around the founder as initially seen
        self.update_visited_cells()
    
    def update_visited_cells(self):
        # Mark all currently visible cells as visited
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                dx = abs(x - self.founder.x)
                dy = abs(y - self.founder.y)
                if dx <= self.founder.visibility and dy <= self.founder.visibility:
                    self.visited_cells[y][x] = True
    
    def generate_maze(self):
        while True:
            # Initialize empty maze
            maze = np.zeros((GRID_SIZE, GRID_SIZE), dtype=int)
            
            # Randomly place walls (1/3 chance for each cell)
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    if random.random() < 1/3:
                        maze[y][x] = 1  # 1 represents wall
            
            # Find a valid starting position for the Founder (not on a wall)
            valid_positions = []
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    if maze[y][x] == 0:  # Empty space
                        valid_positions.append((x, y))
            
            if not valid_positions:
                continue  # Try again if no valid positions
                
            founder_x, founder_y = random.choice(valid_positions)
            
            # Place PMF at a position that's not visible on the first turn
            # (more than 1 step away from the founder)
            pmf_positions = []
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    if maze[y][x] == 0 and max(abs(x - founder_x), abs(y - founder_y)) > 1:
                        pmf_positions.append((x, y))
            
            if not pmf_positions:
                continue  # Try again if no valid PMF positions
                
            pmf_x, pmf_y = random.choice(pmf_positions)
            maze[pmf_y][pmf_x] = 2  # 2 represents PMF
            
            # Check if there's a valid path from Founder to PMF
            if self.check_path(maze.copy(), (founder_x, founder_y), (pmf_x, pmf_y)):
                # Create player maze (same as debug maze but with limited visibility)
                player_maze = maze.copy()
                return maze, player_maze, (pmf_x, pmf_y), (founder_x, founder_y)
    
    def check_path(self, maze, start, end):
        # BFS to check if there's a path from start to end
        queue = [start]
        visited = set([start])
        
        while queue:
            x, y = queue.pop(0)
            
            if (x, y) == end:
                return True
            
            for dx, dy in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                
                if (0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE and 
                    maze[ny][nx] != 1 and (nx, ny) not in visited):
                    queue.append((nx, ny))
                    visited.add((nx, ny))
        
        return False
    
    def draw_maze(self, maze, x_offset, is_player_view=False):
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                rect = pygame.Rect(
                    x * CELL_SIZE + x_offset,
                    y * CELL_SIZE + MARGIN,
                    CELL_SIZE,
                    CELL_SIZE
                )
                
                # Determine visibility in player view
                currently_visible = False
                if is_player_view:
                    dx = abs(x - self.founder.x)
                    dy = abs(y - self.founder.y)
                    currently_visible = dx <= self.founder.visibility and dy <= self.founder.visibility
                
                if is_player_view and not currently_visible and not self.visited_cells[y][x]:
                    # Draw fog of war for non-visible and never-visited cells
                    pygame.draw.rect(self.screen, GRAY, rect)
                elif is_player_view and not currently_visible and self.visited_cells[y][x]:
                    # Draw previously seen cells with distinct colors based on type
                    if maze[y][x] == 1:  # Wall
                        pygame.draw.rect(self.screen, BLACK, rect)
                    elif maze[y][x] == 2:  # PMF
                        pygame.draw.rect(self.screen, LIGHT_GRAY, rect)
                        pmf_text = self.font.render("PMF", True, BLUE)
                        self.screen.blit(pmf_text, (
                            x * CELL_SIZE + x_offset + CELL_SIZE//2 - pmf_text.get_width()//2,
                            y * CELL_SIZE + MARGIN + CELL_SIZE//2 - pmf_text.get_height()//2
                        ))
                    else:  # Empty space
                        pygame.draw.rect(self.screen, WHITE, rect)
                elif maze[y][x] == 1:  # Wall
                    pygame.draw.rect(self.screen, BLACK, rect)
                elif maze[y][x] == 2:  # PMF
                    pygame.draw.rect(self.screen, WHITE, rect)
                    pmf_text = self.font.render("PMF", True, BLUE)
                    self.screen.blit(pmf_text, (
                        x * CELL_SIZE + x_offset + CELL_SIZE//2 - pmf_text.get_width()//2,
                        y * CELL_SIZE + MARGIN + CELL_SIZE//2 - pmf_text.get_height()//2
                    ))
                else:  # Empty space
                    pygame.draw.rect(self.screen, WHITE, rect)
                
                # Draw grid lines
                pygame.draw.rect(self.screen, BLACK, rect, 1)
    
    def draw_founder(self, x_offset):
        # Calculate position for the founder image
        pos_x = self.founder.x * CELL_SIZE + x_offset + (CELL_SIZE - self.founder.founder_size) // 2
        pos_y = self.founder.y * CELL_SIZE + MARGIN + (CELL_SIZE - self.founder.founder_size) // 2
        
        # Draw the founder image (unrotated)
        self.screen.blit(self.founder.image, (pos_x, pos_y))
        
        # Calculate center of the founder for arrow placement
        center_x = self.founder.x * CELL_SIZE + x_offset + CELL_SIZE // 2
        center_y = self.founder.y * CELL_SIZE + MARGIN + CELL_SIZE // 2
        
        # Calculate arrow start and end points based on direction
        start_x, start_y = center_x, center_y
        
        if self.founder.direction == Direction.UP:
            end_x = center_x
            end_y = center_y - self.founder.arrow_length
            # Draw arrowhead
            pygame.draw.polygon(self.screen, RED, [
                (end_x, end_y),
                (end_x - self.founder.arrow_head_size, end_y + self.founder.arrow_head_size),
                (end_x + self.founder.arrow_head_size, end_y + self.founder.arrow_head_size)
            ])
        elif self.founder.direction == Direction.RIGHT:
            end_x = center_x + self.founder.arrow_length
            end_y = center_y
            # Draw arrowhead
            pygame.draw.polygon(self.screen, RED, [
                (end_x, end_y),
                (end_x - self.founder.arrow_head_size, end_y - self.founder.arrow_head_size),
                (end_x - self.founder.arrow_head_size, end_y + self.founder.arrow_head_size)
            ])
        elif self.founder.direction == Direction.DOWN:
            end_x = center_x
            end_y = center_y + self.founder.arrow_length
            # Draw arrowhead
            pygame.draw.polygon(self.screen, RED, [
                (end_x, end_y),
                (end_x - self.founder.arrow_head_size, end_y - self.founder.arrow_head_size),
                (end_x + self.founder.arrow_head_size, end_y - self.founder.arrow_head_size)
            ])
        elif self.founder.direction == Direction.LEFT:
            end_x = center_x - self.founder.arrow_length
            end_y = center_y
            # Draw arrowhead
            pygame.draw.polygon(self.screen, RED, [
                (end_x, end_y),
                (end_x + self.founder.arrow_head_size, end_y - self.founder.arrow_head_size),
                (end_x + self.founder.arrow_head_size, end_y + self.founder.arrow_head_size)
            ])
        
        # Draw the arrow line
        pygame.draw.line(self.screen, RED, (start_x, start_y), (end_x, end_y), self.founder.arrow_width)
    
    def draw_runway(self):
        # Draw runway counter in bottom right
        runway_box_width = 150
        runway_box_height = 60
        runway_box_x = WINDOW_WIDTH - runway_box_width - 20
        runway_box_y = WINDOW_HEIGHT - runway_box_height - 20
        
        # Draw box
        runway_box = pygame.Rect(runway_box_x, runway_box_y, runway_box_width, runway_box_height)
        pygame.draw.rect(self.screen, WHITE, runway_box)
        pygame.draw.rect(self.screen, BLACK, runway_box, 2)
        
        # Draw label
        runway_label = self.font.render("RUNWAY:", True, BLACK)
        self.screen.blit(runway_label, (
            runway_box_x + 10, 
            runway_box_y + 10
        ))
        
        # Draw value
        runway_value = self.font.render(f"{self.runway} months", True, 
                                       RED if self.runway <= 3 else BLACK)
        self.screen.blit(runway_value, (
            runway_box_x + 10, 
            runway_box_y + runway_box_height - 30
        ))
    
    def draw_visibility_indicator(self):
        # Draw visibility indicator near the top right
        vis_box_width = 180
        vis_box_height = 40
        vis_box_x = WINDOW_WIDTH - vis_box_width - 20
        vis_box_y = 20
        
        # Draw box
        vis_box = pygame.Rect(vis_box_x, vis_box_y, vis_box_width, vis_box_height)
        pygame.draw.rect(self.screen, WHITE, vis_box)
        pygame.draw.rect(self.screen, BLACK, vis_box, 2)
        
        # Draw value
        boost_text = " (+1)" if self.founder.temporary_boost > 0 else ""
        vis_text = self.font.render(f"Visibility: {self.founder.visibility}{boost_text}", True, BLUE)
        self.screen.blit(vis_text, (
            vis_box_x + 10, 
            vis_box_y + vis_box_height//2 - vis_text.get_height()//2
        ))
    
    def draw_buttons(self):
        button_width = 120
        button_height = 40
        button_margin = 15
        
        # Define button positions
        button_y = GRID_SIZE * CELL_SIZE + MARGIN * 2
        total_buttons_width = 5 * button_width + 4 * button_margin  # Now 5 buttons (including debug)
        button_start_x = (WINDOW_WIDTH - total_buttons_width) // 2
        
        button_positions = []
        for i in range(5):  # Now 5 buttons
            button_x = button_start_x + i * (button_width + button_margin)
            button_positions.append((button_x, button_y, button_width, button_height))
        
        # Draw buttons
        actions = ["Pivot", "Build", "Talk to User", "Fundraise", "Debug Mode"]
        
        for i, (x, y, w, h) in enumerate(button_positions):
            button_rect = pygame.Rect(x, y, w, h)
            
            # Highlight the Debug Mode button if enabled
            if i == 4 and self.debug_mode:
                pygame.draw.rect(self.screen, GREEN, button_rect)
            # Highlight the Talk to User button if temporary boost is active
            elif i == 2 and self.founder.temporary_boost > 0:
                pygame.draw.rect(self.screen, GREEN, button_rect)
            else:
                pygame.draw.rect(self.screen, BLUE, button_rect)
                
            pygame.draw.rect(self.screen, BLACK, button_rect, 2)
            
            button_text = self.font.render(actions[i], True, WHITE)
            self.screen.blit(button_text, (
                x + w//2 - button_text.get_width()//2,
                y + h//2 - button_text.get_height()//2
            ))
        
        return button_positions
    
    def check_win(self):
        if (self.founder.x, self.founder.y) == self.pmf_pos:
            self.game_won = True
    
    def run(self):
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and not self.game_won and not self.game_over:
                    mouse_pos = pygame.mouse.get_pos()
                    button_positions = self.draw_buttons()
                    
                    # Check if any button was clicked
                    for i, (x, y, w, h) in enumerate(button_positions):
                        if x <= mouse_pos[0] <= x + w and y <= mouse_pos[1] <= y + h:
                            if i == 0:  # Pivot
                                self.founder.pivot()
                                self.runway -= 1
                            elif i == 1:  # Build
                                self.founder.build(self.debug_maze)
                                self.check_win()
                                self.runway -= 1
                                # Update visited cells after the move
                                self.update_visited_cells()
                            elif i == 2:  # Talk to User
                                self.founder.talk_to_user()
                                self.runway -= 1
                                # Update visited cells after increasing visibility
                                self.update_visited_cells()
                            elif i == 3:  # Fundraise
                                self.founder.fundraise()
                                self.runway -= 1
                            elif i == 4:  # Debug Mode
                                self.debug_mode = not self.debug_mode
                                
                            # Check if out of runway
                            if self.runway <= 0:
                                self.game_over = True
            
            # Clear the screen
            self.screen.fill(WHITE)
            
            # Draw title for debug maze
            debug_title = self.font.render("Debug View", True, BLACK)
            self.screen.blit(debug_title, (MARGIN + GRID_SIZE * CELL_SIZE // 2 - debug_title.get_width() // 2, MARGIN // 2))
            
            # Draw title for player maze
            player_title = self.font.render("Player View", True, BLACK)
            self.screen.blit(player_title, (MARGIN * 2 + GRID_SIZE * CELL_SIZE * 3 // 2 - player_title.get_width() // 2, MARGIN // 2))
            
            # Draw the mazes
            if self.debug_mode:
                self.draw_maze(self.debug_maze, MARGIN)
            else:
                # Draw an empty box for the debug view when disabled
                debug_rect = pygame.Rect(MARGIN, MARGIN, GRID_SIZE * CELL_SIZE, GRID_SIZE * CELL_SIZE)
                pygame.draw.rect(self.screen, GRAY, debug_rect)
                disabled_text = self.font.render("Debug View Disabled", True, BLACK)
                self.screen.blit(disabled_text, (
                    MARGIN + GRID_SIZE * CELL_SIZE // 2 - disabled_text.get_width() // 2,
                    MARGIN + GRID_SIZE * CELL_SIZE // 2 - disabled_text.get_height() // 2
                ))
                
            self.draw_maze(self.player_maze, MARGIN * 2 + GRID_SIZE * CELL_SIZE, True)
            
            # Draw the founder on both mazes
            if self.debug_mode:
                self.draw_founder(MARGIN)
            self.draw_founder(MARGIN * 2 + GRID_SIZE * CELL_SIZE)
            
            # Draw runway counter
            self.draw_runway()
            
            # Draw visibility indicator
            self.draw_visibility_indicator()
            
            # Draw buttons
            self.draw_buttons()
            
            # Draw win message if game is won
            if self.game_won:
                win_text = self.large_font.render("YOU WIN!", True, GREEN)
                win_bg = pygame.Rect(
                    WINDOW_WIDTH // 2 - win_text.get_width() // 2 - 20,
                    WINDOW_HEIGHT // 2 - win_text.get_height() // 2 - 20,
                    win_text.get_width() + 40,
                    win_text.get_height() + 40
                )
                pygame.draw.rect(self.screen, WHITE, win_bg)
                pygame.draw.rect(self.screen, GREEN, win_bg, 4)
                self.screen.blit(win_text, (
                    WINDOW_WIDTH // 2 - win_text.get_width() // 2,
                    WINDOW_HEIGHT // 2 - win_text.get_height() // 2
                ))
            
            # Draw game over message if out of runway
            if self.game_over:
                game_over_text = self.large_font.render("YOU DIE!", True, RED)
                game_over_bg = pygame.Rect(
                    WINDOW_WIDTH // 2 - game_over_text.get_width() // 2 - 20,
                    WINDOW_HEIGHT // 2 - game_over_text.get_height() // 2 - 20,
                    game_over_text.get_width() + 40,
                    game_over_text.get_height() + 40
                )
                pygame.draw.rect(self.screen, DARK_RED, game_over_bg)
                pygame.draw.rect(self.screen, BLACK, game_over_bg, 4)
                self.screen.blit(game_over_text, (
                    WINDOW_WIDTH // 2 - game_over_text.get_width() // 2,
                    WINDOW_HEIGHT // 2 - game_over_text.get_height() // 2
                ))
            
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = IdeaMaze()
    game.run() 