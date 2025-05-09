import pygame
import sys
import time
import random
from idea_maze import IdeaMaze, Direction

class DumbPlayer:
    def __init__(self):
        # Create the game instance
        self.game = IdeaMaze()
        # Disable debug mode to simulate player view
        self.game.debug_mode = False
        # Set AI mode to disable user button clicks
        self.ai_mode = True
        self.game.ai_mode = True
        # Available actions for the AI
        self.actions = ["pivot", "build", "talk_to_user", "fundraise"]
        # Delay between AI moves in seconds
        self.move_delay = 1
    
    def get_visible_map(self):
        """
        Extract the currently visible map information from the game
        """
        visible_map = []
        for y in range(self.game.player_maze.shape[0]):
            row = []
            for x in range(self.game.player_maze.shape[1]):
                # Check if the cell is visible to the founder
                dx = abs(x - self.game.founder.x)
                dy = abs(y - self.game.founder.y)
                if dx <= self.game.founder.visibility and dy <= self.game.founder.visibility:
                    # Cell is visible, get its actual value
                    row.append(self.game.player_maze[y][x])
                elif self.game.visited_cells[y][x]:
                    # Cell was previously seen
                    row.append(self.game.player_maze[y][x])
                else:
                    # Cell is not visible and never seen before
                    row.append(-1)  # -1 indicates fog of war
            visible_map.append(row)
        return visible_map
    
    def get_game_state(self):
        """
        Get the current state of the game for the AI to make decisions
        """
        return {
            "visible_map": self.get_visible_map(),
            "founder_position": (self.game.founder.x, self.game.founder.y),
            "founder_direction": self.game.founder.direction,
            "visibility": self.game.founder.visibility,
            "runway": self.game.runway,
            "temporary_boost": self.game.founder.temporary_boost > 0
        }
    
    def choose_action(self, game_state):
        """
        Based on the game state, choose an action to take
        For now, just randomly select an action
        This can be replaced with actual AI logic in the future
        """
        return random.choice(self.actions)
    
    def execute_action(self, action):
        """
        Execute the chosen action in the game
        """
        if action == "pivot":
            self.game.founder.pivot()
            self.game.runway -= 1
        elif action == "build":
            self.game.founder.build(self.game.debug_maze)
            self.game.check_win()
            self.game.runway -= 1
            # Update visited cells after the move
            self.game.update_visited_cells()
        elif action == "talk_to_user":
            self.game.founder.talk_to_user()
            self.game.runway -= 1
            # Update visited cells after increasing visibility
            self.game.update_visited_cells()
        elif action == "fundraise":
            self.game.founder.fundraise()
            self.game.runway -= 1
        
        # Check if out of runway
        if self.game.runway <= 0:
            self.game.game_over = True
    
    def run(self):
        """
        Main loop for the AI player
        """
        # Monkey patch the IdeaMaze.run method to skip user input detection
        original_run = self.game.run
        
        def ai_run_game(self_game):
            running = True
            clock = pygame.time.Clock()
            
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                        pygame.quit()
                        sys.exit()
                
                # Clear the screen
                self_game.screen.fill((255, 255, 255))
                
                # Draw title for debug maze (even though it's off)
                debug_title = self_game.font.render("Debug View (Disabled)", True, (0, 0, 0))
                self_game.screen.blit(debug_title, (50 + 12 * 50 // 2 - debug_title.get_width() // 2, 50 // 2))
                
                # Draw title for player maze
                player_title = self_game.font.render("AI Player View", True, (0, 0, 0))
                self_game.screen.blit(player_title, (50 * 2 + 12 * 50 * 3 // 2 - player_title.get_width() // 2, 50 // 2))
                
                # Draw empty area for debug view
                debug_rect = pygame.Rect(50, 50, 12 * 50, 12 * 50)
                pygame.draw.rect(self_game.screen, (200, 200, 200), debug_rect)
                disabled_text = self_game.font.render("Debug View Disabled", True, (0, 0, 0))
                self_game.screen.blit(disabled_text, (
                    50 + 12 * 50 // 2 - disabled_text.get_width() // 2,
                    50 + 12 * 50 // 2 - disabled_text.get_height() // 2
                ))
                
                # Draw the player's maze view
                self_game.draw_maze(self_game.player_maze, 50 * 2 + 12 * 50, True)
                
                # Draw the founder on player maze
                self_game.draw_founder(50 * 2 + 12 * 50)
                
                # Draw runway counter
                self_game.draw_runway()
                
                # Draw visibility indicator
                self_game.draw_visibility_indicator()
                
                # Draw buttons (inactive)
                self_game.draw_buttons()
                
                # Draw AI status
                ai_box_width = 180
                ai_box_height = 40
                ai_box_x = 20
                ai_box_y = 20
                
                # Draw box
                ai_box = pygame.Rect(ai_box_x, ai_box_y, ai_box_width, ai_box_height)
                pygame.draw.rect(self_game.screen, (255, 255, 255), ai_box)
                pygame.draw.rect(self_game.screen, (0, 0, 0), ai_box, 2)
                
                # Draw value
                ai_text = self_game.font.render("AI Mode Active", True, (0, 0, 255))
                self_game.screen.blit(ai_text, (
                    ai_box_x + 10, 
                    ai_box_y + ai_box_height//2 - ai_text.get_height()//2
                ))
                
                # Draw win message if game is won
                if self_game.game_won:
                    win_text = self_game.large_font.render("AI WINS!", True, (0, 255, 0))
                    win_bg = pygame.Rect(
                        self_game.screen.get_width() // 2 - win_text.get_width() // 2 - 20,
                        self_game.screen.get_height() // 2 - win_text.get_height() // 2 - 20,
                        win_text.get_width() + 40,
                        win_text.get_height() + 40
                    )
                    pygame.draw.rect(self_game.screen, (255, 255, 255), win_bg)
                    pygame.draw.rect(self_game.screen, (0, 255, 0), win_bg, 4)
                    self_game.screen.blit(win_text, (
                        self_game.screen.get_width() // 2 - win_text.get_width() // 2,
                        self_game.screen.get_height() // 2 - win_text.get_height() // 2
                    ))
                
                # Draw game over message if out of runway
                if self_game.game_over:
                    game_over_text = self_game.large_font.render("AI DIED!", True, (255, 0, 0))
                    game_over_bg = pygame.Rect(
                        self_game.screen.get_width() // 2 - game_over_text.get_width() // 2 - 20,
                        self_game.screen.get_height() // 2 - game_over_text.get_height() // 2 - 20,
                        game_over_text.get_width() + 40,
                        game_over_text.get_height() + 40
                    )
                    pygame.draw.rect(self_game.screen, (180, 0, 0), game_over_bg)
                    pygame.draw.rect(self_game.screen, (0, 0, 0), game_over_bg, 4)
                    self_game.screen.blit(game_over_text, (
                        self_game.screen.get_width() // 2 - game_over_text.get_width() // 2,
                        self_game.screen.get_height() // 2 - game_over_text.get_height() // 2
                    ))
                
                pygame.display.flip()
                clock.tick(60)
                
                # If not game over or won, let the AI make a move
                if not self_game.game_won and not self_game.game_over:
                    # Add delay to make AI moves visible
                    time.sleep(self.move_delay)
                    # Get current game state
                    game_state = self.get_game_state()
                    # Let AI choose an action
                    action = self.choose_action(game_state)
                    # Execute the action
                    self.execute_action(action)
                    
                    # Display the action chosen
                    action_text = self_game.font.render(f"AI Action: {action.replace('_', ' ').title()}", True, (0, 0, 255))
                    self_game.screen.blit(action_text, (
                        self_game.screen.get_width() // 2 - action_text.get_width() // 2,
                        self_game.screen.get_height() - 80
                    ))
                    pygame.display.flip()
            
            pygame.quit()
            sys.exit()
        
        # Replace the game's run method with our AI-controlled version
        self.game.run = lambda: ai_run_game(self.game)
        
        # Start the game
        self.game.run()

if __name__ == "__main__":
    ai = DumbPlayer()
    ai.run() 