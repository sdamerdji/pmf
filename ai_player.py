import pygame
import sys
import time
import random
import os
import json
from openai import OpenAI
from idea_maze import IdeaMaze, Direction

class DumbPlayer:
    """
    A player that makes random moves without any strategy
    """
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
        self.move_delay = 2
        # Track action history
        self.action_history = []
        # Current action being performed (for UI highlighting)
        self.current_action = None
    
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
            "founder_direction": self.game.founder.direction.name,
            "visibility": self.game.founder.visibility,
            "runway": self.game.runway,
            "temporary_boost": self.game.founder.temporary_boost > 0
        }
    
    def choose_action(self, game_state):
        """
        Based on the game state, choose an action to take
        For now, just randomly select an action
        """
        action = random.choice(self.actions)
        self.current_action = action
        return action
    
    def execute_action(self, action):
        """
        Execute the chosen action in the game
        """
        # Add to action history
        self.action_history.append(action)
        # Set current action for UI highlighting
        self.current_action = action
        
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
    
    def draw_buttons(self, screen, font):
        """
        Draw the game buttons with appropriate highlighting
        """
        button_width = 120
        button_height = 40
        button_margin = 15
        
        # Define button positions
        button_y = 12 * 50 + 50 * 2
        total_buttons_width = 5 * button_width + 4 * button_margin
        button_start_x = (screen.get_width() - total_buttons_width) // 2
        
        button_positions = []
        for i in range(5):
            button_x = button_start_x + i * (button_width + button_margin)
            button_positions.append((button_x, button_y, button_width, button_height))
        
        # Map button index to action
        action_map = {
            0: "pivot",
            1: "build", 
            2: "talk_to_user",
            3: "fundraise",
            4: None  # Debug button doesn't correspond to an AI action
        }
        
        # Draw buttons
        actions = ["Pivot", "Build", "Talk to User", "Fundraise", "Debug Mode"]
        
        for i, (x, y, w, h) in enumerate(button_positions):
            button_rect = pygame.Rect(x, y, w, h)
            
            # Choose button color based on current action and button function
            button_color = (0, 0, 255)  # Default blue
            
            # Highlight the current action button
            if i < 4 and action_map[i] == self.current_action:
                button_color = (0, 200, 0)  # Green for active action
            # Special case for debug mode button
            elif i == 4 and self.game.debug_mode:
                button_color = (0, 200, 0)  # Green for active debug mode
            # Special case for talk to user when visibility is boosted
            elif i == 2 and self.game.founder.temporary_boost > 0:
                button_color = (0, 150, 0)  # Slightly duller green for active visibility boost
                
            pygame.draw.rect(screen, button_color, button_rect)
            pygame.draw.rect(screen, (0, 0, 0), button_rect, 2)
            
            button_text = font.render(actions[i], True, (255, 255, 255))
            screen.blit(button_text, (
                x + w//2 - button_text.get_width()//2,
                y + h//2 - button_text.get_height()//2
            ))
            
            # Add semi-transparent overlay to indicate buttons are disabled in AI mode
            disabled_overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            disabled_overlay.fill((0, 0, 0, 64))  # Semi-transparent black
            screen.blit(disabled_overlay, (x, y))
        
        return button_positions
    
    def run(self):
        """
        Main loop for the AI player
        """
        # Monkey patch the IdeaMaze.run method to skip user input detection
        original_run = self.game.run
        
        def ai_run_game(self_game):
            running = True
            clock = pygame.time.Clock()
            last_action_time = 0
            player_label = getattr(self, 'player_label', "DumbPlayer")
            
            while running:
                current_time = time.time()
                
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
                player_title = self_game.font.render(f"{player_label} View", True, (0, 0, 0))
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
                
                # Draw custom buttons with proper highlighting
                self.draw_buttons(self_game.screen, self_game.font)
                
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
                ai_text = self_game.font.render(f"{player_label} Active", True, (0, 0, 255))
                self_game.screen.blit(ai_text, (
                    ai_box_x + 10, 
                    ai_box_y + ai_box_height//2 - ai_text.get_height()//2
                ))
                
                # Display current action if available
                if self.current_action:
                    action_text = self_game.font.render(
                        f"Current Action: {self.current_action.replace('_', ' ').title()}", 
                        True, (0, 0, 255)
                    )
                    self_game.screen.blit(action_text, (
                        self_game.screen.get_width() // 2 - action_text.get_width() // 2,
                        self_game.screen.get_height() - 80
                    ))
                
                # Draw win message if game is won
                if self_game.game_won:
                    win_text = self_game.large_font.render(f"{player_label} WINS!", True, (0, 255, 0))
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
                    game_over_text = self_game.large_font.render(f"{player_label} DIED!", True, (255, 0, 0))
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
                
                # If not game over or won, let the AI make a move after the delay time has passed
                if (not self_game.game_won and not self_game.game_over and 
                    current_time - last_action_time >= self.move_delay):
                    # Get current game state
                    game_state = self.get_game_state()
                    # Let AI choose an action
                    action = self.choose_action(game_state)
                    # Execute the action
                    self.execute_action(action)
                    # Record the time this action was taken
                    last_action_time = time.time()
            
            pygame.quit()
            sys.exit()
        
        # Replace the game's run method with our AI-controlled version
        self.game.run = lambda: ai_run_game(self.game)
        
        # Start the game
        self.game.run()


class AIPlayer(DumbPlayer):
    """
    A player that uses OpenAI to make intelligent moves based on the game state
    """
    def __init__(self):
        super().__init__()
        
        # OpenAI client
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        # Load README content for system prompt
        with open("README.md", "r") as f:
            self.readme_content = f.read()
        
        # Set a more descriptive UI label
        self.player_label = "OpenAI Player"
    
    def choose_action(self, game_state):
        """
        Choose an action based on OpenAI's recommendation
        """
        # Create a string representation of the visible map
        map_str = self.map_to_string(game_state["visible_map"], game_state["founder_position"])
        
        # Format the action history
        action_history = "\n".join([f"- {i+1}. {action.replace('_', ' ').title()}" 
                                     for i, action in enumerate(self.action_history)])
        if not action_history:
            action_history = "No actions taken yet."
        
        # Create a user prompt with the game state and action history
        user_prompt = f"""
Current Game State:
- Position: ({game_state['founder_position'][0]}, {game_state['founder_position'][1]})
- Direction: {game_state['founder_direction']}
- Visibility: {game_state['visibility']}
- Runway: {game_state['runway']} months
- Temporary visibility boost: {'Yes' if game_state['temporary_boost'] else 'No'}

Visible Map (? = unexplored, # = wall, . = empty space, P = PMF, F = Founder's position):
{map_str}

Action History:
{action_history}

Based on the current game state, choose your next action:
1. pivot
2. build
3. talk_to_user
4. fundraise

Choose one action from the list above. Respond with only the action name.
"""

        # Extract only specific sections from the README for the system prompt
        readme_sections = self.extract_readme_sections([
            "Game Elements", 
            "Controls", 
            "Visibility and Fog of War", 
            "Win/Lose Conditions"
        ])

        # System prompt uses only the specified README sections
        system_prompt = f"""
You are playing "The Idea Maze" game. Your goal is to navigate the Founder to the PMF square.

Here are the relevant game rules:

{readme_sections}

You must respond with exactly one of these actions: "pivot", "build", "talk_to_user", or "fundraise".
Do not include any explanation, just the action name.
"""

        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4.1-2025-04-14",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,  # Lower temperature for more consistent responses
                max_tokens=10,     # We only need a few tokens for the action
            )
            
            print(system_prompt)
            print(user_prompt)
            # Extract the chosen action
            action_text = response.choices[0].message.content.strip().lower()
            
            # Direct matching with valid actions
            valid_actions = ["pivot", "build", "talk_to_user", "fundraise"]
            
            # Try exact match first
            if action_text in valid_actions:
                self.current_action = action_text
                return action_text
                
            # Try to extract valid action if the response includes extra text
            for valid_action in valid_actions:
                if valid_action in action_text:
                    # Log that we had to clean up the response
                    print(f"Cleaned up OpenAI response from '{action_text}' to '{valid_action}'")
                    self.current_action = valid_action
                    return valid_action
            
            # If no valid action found, default to a random action
            print(f"OpenAI returned invalid action: '{action_text}', using random action instead")
            random_action = random.choice(valid_actions)
            self.current_action = random_action
            return random_action
            
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            # Fallback to random action if API call fails
            random_action = random.choice(self.actions)
            self.current_action = random_action
            return random_action
    
    def extract_readme_sections(self, section_names):
        """Extract only specific sections from the README content"""
        result = []
        lines = self.readme_content.split('\n')
        
        current_section = None
        for line in lines:
            # Check if this line starts a new section
            if line.startswith('###') and any(section in line for section in section_names):
                current_section = line.strip('# ')
            # Check if this line ends the current section (starts a new one)
            elif line.startswith('###') and current_section is not None:
                current_section = None
            # Add content from active sections
            elif current_section is not None:
                result.append(line)
        
        return '\n'.join(result)
    
    def map_to_string(self, visible_map, founder_position):
        """
        Convert the numeric map to a string representation
        -1 = unknown/fog of war (?), 
        0 = empty space (.), 
        1 = wall (#), 
        2 = PMF (P),
        F = Founder's current position
        """
        map_symbols = {
            -1: "?",  # Fog of war / unexplored
            0: ".",   # Empty space
            1: "#",   # Wall
            2: "P"    # PMF
        }
        
        founder_x, founder_y = founder_position
        
        map_rows = []
        for y, row in enumerate(visible_map):
            row_chars = []
            for x, cell in enumerate(row):
                # If this is the founder's position, mark it with 'F'
                if x == founder_x and y == founder_y:
                    row_chars.append("F")
                else:
                    row_chars.append(map_symbols.get(cell, "?"))
            map_rows.append("".join(row_chars))
        
        return "\n".join(map_rows)


if __name__ == "__main__":
    # Choose which player to use (default to AIPlayer)
    player_type = os.environ.get("PLAYER_TYPE", "ai").lower()
    print(player_type)
    if player_type == "dumb":
        player = DumbPlayer()
    else:
        if not os.environ.get("OPENAI_API_KEY"):
            print("WARNING: OPENAI_API_KEY environment variable not set.")
            print("Defaulting to DumbPlayer.")
            player = DumbPlayer()
        else:
            print('using AIPlayer')
            player = AIPlayer()
    
    player.run() 