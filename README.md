# The Idea Maze

A simple pygame-based game where you guide a Founder through a maze to reach Product-Market Fit (PMF).

## Installation

1. Make sure you have Python installed (Python 3.6+ recommended)
2. Install the required dependencies:
   ```
   pip install pygame numpy
   ```

## How to Play

Run the game with:

```
python idea_maze.py
```

### Game Elements:

- **Founder**: Alex's image with a red arrow indicating the current direction
- **PMF**: The square marked "PMF" - your destination
- **Walls**: Black squares that block your path
- **Runway**: The number of months you have left before running out of money
- **Visibility**: How far the Founder can see in all directions

### Controls:

Click on one of the buttons to take action:

1. **Pivot**: Randomly change the Founder's direction (costs 1 month of runway)
2. **Build**: Move the Founder forward one step in the current direction and resets vision to normal (costs 1 month of runway)
3. **Talk to User**: Temporarily increase visibility by 1 square in all directions (costs 1 month of runway)
4. **Fundraise**: Does nothing, but still costs 1 month of runway
5. **Debug Mode**: Toggle the visibility of the debug maze view

### Game Views:

- **Debug View**: Shows the entire maze for debugging (can be toggled off)
- **Player View**: Shows what the Founder can currently see, plus previously explored areas

### Visibility and Fog of War:

- Base visibility is 1 square in all directions
- "Talk to User" temporarily increases visibility by 1 square (max 2)
- "Build" resets visibility to the base level
- Once squares are seen, they remain visible for the rest of the game:
  - Currently visible squares appear in full color
  - Previously seen walls appear as dark gray
  - Previously seen empty paths appear as light gray
  - Unexplored areas appear as medium gray (fog of war)

### Win/Lose Conditions:

- **Win**: You win when the Founder reaches the PMF square!
- **Lose**: You lose when your runway reaches 0 months

Good luck finding Product-Market Fit before you run out of money!
