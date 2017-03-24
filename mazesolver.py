import sys
from collections import deque
import configparser
import time

from PIL import Image, ImageDraw, ImageFont
import tweepy


print(sys.version)

class Maze:
    GRID_CHAR_SCALE = 3
    CHARACTER_DIM = (16,8)
    NUM_COL = CHARACTER_DIM[0] * GRID_CHAR_SCALE
    NUM_ROW = CHARACTER_DIM[1] * GRID_CHAR_SCALE

    # TODO: simplify dict by abstracting to number, then number to array
    charDict = {"╔": [[0, 0, 0], [0, 1, 1], [0, 1, 0]],
                "┌": [[0, 0, 0], [0, 1, 1], [0, 1, 0]],
                "╓": [[0, 0, 0], [0, 1, 1], [0, 1, 0]],
                "╒": [[0, 0, 0], [0, 1, 1], [0, 1, 0]],
                "═": [[0, 0, 0], [1, 1, 1], [0, 0, 0]],
                "─": [[0, 0, 0], [1, 1, 1], [0, 0, 0]],
                "╗": [[0, 0, 0], [1, 1, 0], [0, 1, 0]],
                "┐": [[0, 0, 0], [1, 1, 0], [0, 1, 0]],
                "╕": [[0, 0, 0], [1, 1, 0], [0, 1, 0]],
                "╖": [[0, 0, 0], [1, 1, 0], [0, 1, 0]],
                "╩": [[0, 1, 0], [1, 1, 1], [0, 0, 0]],
                "╧": [[0, 1, 0], [1, 1, 1], [0, 0, 0]],
                "┴": [[0, 1, 0], [1, 1, 1], [0, 0, 0]],
                "╨": [[0, 1, 0], [1, 1, 1], [0, 0, 0]],
                "╚": [[0, 1, 0], [0, 1, 1], [0, 0, 0]],
                "╙": [[0, 1, 0], [0, 1, 1], [0, 0, 0]],
                "╘": [[0, 1, 0], [0, 1, 1], [0, 0, 0]],
                "└": [[0, 1, 0], [0, 1, 1], [0, 0, 0]],
                "╣": [[0, 1, 0], [1, 1, 0], [0, 1, 0]],
                "╡": [[0, 1, 0], [1, 1, 0], [0, 1, 0]],
                "╢": [[0, 1, 0], [1, 1, 0], [0, 1, 0]],
                "┤": [[0, 1, 0], [1, 1, 0], [0, 1, 0]],
                "╝": [[0, 1, 0], [1, 1, 0], [0, 0, 0]],
                "┘": [[0, 1, 0], [1, 1, 0], [0, 0, 0]],
                "╛": [[0, 1, 0], [1, 1, 0], [0, 0, 0]],
                "╜": [[0, 1, 0], [1, 1, 0], [0, 0, 0]],
                "╠": [[0, 1, 0], [0, 1, 1], [0, 1, 0]],
                "├": [[0, 1, 0], [0, 1, 1], [0, 1, 0]],
                "╞": [[0, 1, 0], [0, 1, 1], [0, 1, 0]],
                "╟": [[0, 1, 0], [0, 1, 1], [0, 1, 0]],
                "╬": [[0, 1, 0], [1, 1, 1], [0, 1, 0]],
                "╪": [[0, 1, 0], [1, 1, 1], [0, 1, 0]],
                "┼": [[0, 1, 0], [1, 1, 1], [0, 1, 0]],
                "╫": [[0, 1, 0], [1, 1, 1], [0, 1, 0]],
                "║": [[0, 1, 0], [0, 1, 0], [0, 1, 0]],
                "╦": [[0, 0, 0], [1, 1, 1], [0, 1, 0]],
                "╥": [[0, 0, 0], [1, 1, 1], [0, 1, 0]],
                "┬": [[0, 0, 0], [1, 1, 1], [0, 1, 0]],
                "╤": [[0, 0, 0], [1, 1, 1], [0, 1, 0]]
                }

    def __init__(self, mazeString):

        self.map = self.expandMaze(mazeString)
        self.start = (2,2)
        self.finish = (21, 45)

    def expandMaze(self, mazeString):
        #I could go ahead and map in the list comprehension...
        #characterArray = [[cell for cell in row] for row in mazeString.splitlines()]
        condensedGrid = [[self.charToGrid(cell) for cell in row] for row in mazeString.splitlines()]

        #condensedGrid = []

        #for row in characterArray:
        #    condensedGrid.append([self.characterToGrid(character) for character in row])


        expandedGrid = [[0 for col in range(self.NUM_COL)] for row in range(self.NUM_ROW)]

        for char_row, row in enumerate(condensedGrid):
            for char_col, col in enumerate(row):

                grid_row_start, _ = self.charIdxToGridIdx(char_row)
                grid_col_start, grid_col_end = self.charIdxToGridIdx(char_col)

                for idx in range(self.GRID_CHAR_SCALE):
                    expandedGrid[grid_row_start + idx][grid_col_start:grid_col_end] = col[idx]

        return expandedGrid

    def charToGrid(self, character):
        # given a character, return a 3x3 array
        return self.charDict[character]

    def charIdxToGridIdx(self, char_index):
        grid_start = char_index * self.GRID_CHAR_SCALE
        grid_end = grid_start + self.GRID_CHAR_SCALE
        return grid_start, grid_end

class MazeSolver:

    wall_code =  "☐" #   "⬜" "■" "▢"
    empty_code = " "
    path_code =  "●"# "○"
    start_code =  "◉"#"◯"
    finish_code = "◉" #"◯"

    visual_dict = {0: empty_code, 1: wall_code, path_code: path_code, start_code: start_code, finish_code: finish_code}

    def __init__(self, mazeObj):
        self.maze = mazeObj
        self.visited = []
        self.finished = False
        self.solution = []

    def solve(self):
        self.solution = self.find_path_bfs()

    def solutionToMap(self):
        if self.solution:
            solutionGrid = self.maze.map

            for position in self.solution:
                solutionGrid[position[0]][position[1]] = self.path_code

            # add start and finish
            solutionGrid[self.maze.start[0]][self.maze.start[1]] = self.start_code
            solutionGrid[self.maze.finish[0]][self.maze.finish[1]] = self.finish_code

            return solutionGrid

    def toImage(self):
        solutionGrid = self.solutionToMap()


        # Prepare image
        solutionImage = Image.new('RGBA', (720, 360), (255, 255, 255, 0))
        drawer = ImageDraw.Draw(solutionImage)
        font = ImageFont.truetype("Arial Unicode.ttf",20)

        # Calculate spacing factors - TODO: try to find a way to keep 2:1 ratio...
        scaling_factor = max([drawer.textsize(val, font)[0] for key, val in self.visual_dict.items()])
        #spacing_width_dict = {key: drawer.textsize(val, font)[0] for key, val in self.visual_dict.items()}
        #spacing_height_dict = {key: drawer.textsize(val, font)[1] for key, val in self.visual_dict.items()}

        # Populate image
        for row_idx, row in enumerate(solutionGrid):
            for col_idx, block in enumerate(row):
                drawer.text((col_idx * scaling_factor, row_idx * scaling_factor), self.visual_dict[block], fill=(1, 0, 0), font=font)

        return solutionImage

    def dfs(self):
        #track possible moves
        options = [self.maze.start]
        #track visited
        self.visited.append(self.maze.start)

        while options:
            nextPosition = options.pop()
            #For visual affirmation, color in the visited stuff
            #self.maze.map[nextPosition[0]][nextPosition[1]] = 8
            self.visited.append(nextPosition)
            if nextPosition == self.maze.finish:
                self.finished = True
                for row in self.maze.map:
                    print(row)
                break
            options.extend(self.getNeighbors(nextPosition))

        if self.finished:
            self.solution = self.visited
            print("U DED ET YEAA")
            print(len(self.visited))




    def find_path_bfs(self):
        #queue = deque([("", self.maze.start)])
        queue = deque([([], self.maze.start)])
        #visited = set()

        while queue:
            path, current = queue.popleft()
            #print("PATH top", path)
            #print("N:", self.getNeighbors(current))
            if current == self.maze.finish:
                self.finished = True
                return path
            if current in self.visited:
                continue
            #visited.add(current)
            self.visited.append(current)
            #for direction, neighbour in graph[current]:
            #print("PATH bottom", path)
            for neighbor in self.getNeighbors(current):
                #print("PATH vbottom", path)
                queue.append((path + [neighbor], neighbor))
                #print("PATH zbottom", path)
                #print(queue)
        #return "NO WAY!"
        return path

    def getNeighbors(self, position):
        north = (position[0] - 1, position[1])
        south = (position[0] + 1, position[1])
        east = (position[0], position[1] - 1)
        west = (position[0], position[1] + 1)
        neighbors = [north, south, east, west]
        return [direction for direction in neighbors if self.visitable(direction)]

    def visitable(self, position):
        return (self.maze.map[position[0]][position[1]] == 0) and (position not in self.visited)

class BirdUp:
    s_name = "miniaturemazes"

    def __init__(self):
        config = configparser.ConfigParser()
        config.read('config.ini')

        self._consumer_key = config['twitterAuth']['consumer_key']
        self._consumer_secret = config['twitterAuth']['consumer_secret']
        self._access_token = config['twitterAuth']['access_token']
        self._access_secret = config['twitterAuth']['access_secret']

        try:
            auth = tweepy.OAuthHandler(self._consumer_key,
                                       self._consumer_secret)
            auth.set_access_token(self._access_token, self._access_secret)

            self.client = tweepy.API(auth)
            if not self.client.verify_credentials():
                raise tweepy.TweepError
        except tweepy.TweepError as e:
            print('ERROR : connection failed. Check your OAuth keys.')
        else:
            print('Connected as @{}, you can start to tweet !'.format(self.client.me().screen_name))
            self.client_id = self.client.me().id

            self.tweet = self.getMazeTweets(1)[0]
            self.tweetID = self.tweet.id
            self.maze = Maze(self.tweet.text)
            self.solver = MazeSolver(self.maze)

    def getMazeTweets(self, number):
        return self.client.user_timeline(screen_name = "miniaturemazes",count=number)

    def getMazeText(self, number):
        return [tweet.text for tweet in self.getMazeTweets(number)]

    def tweetMaze(self):
        #tweet the solution in response to specific maze or just @ the account??
        # if finished, make the comment a smiley emoji. Otherwise, a sad emoji
        pass
    def getSolveTweet(self):
        if self.tweet:
            self.solver.solve()
            img = self.solver.toImage()
            img.save('test.gif', 'GIF', transparency=0)
            if self.solver.finished:
                robot_emotion = "😄"
            else:
                robot_emotion = "😢"

            #self.client.update_with_media(filename='test.gif', status=robot_emotion)#, in_reply_to_status_id=self.tweetID)
            self.client.update_status(robot_emotion)
        else:
            self.client.update_status("hmmm")

while True:
    ts = BirdUp()
    ts.getSolveTweet()
    time.sleep(60)
# mazeList = ts.getMazeText(200)


# finishable = 0

# for i, maze in enumerate(mazeList):
#     print(maze)
#     m = Maze(maze)
#     solver = MazeSolver(m, 'myBootySoFresh')
#     solver.solve()
#     if solver.finished:
#         finishable += 1
#     if i%20 == 0:
#         img = solver.toImage()
#         img.save('test' + str(i) + '.gif', 'GIF', transparency=0)
# print(finishable)
