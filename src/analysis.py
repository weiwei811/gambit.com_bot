from src.dataclass import Board,Player
from src.strategy import sim_runs
import matplotlib.pyplot as plt
from tqdm import tqdm

def create_mock_board():
    b=Board()
    for i in range(6):
        player=Player()
        b.players.append(player)

    b.players[0].is_me=True
    b.players[0].hand.append(b.deal())
    b.players[0].hand.append(b.deal())
    
    return b
def analyze(n):
    winrates=[]

    for _ in tqdm(range(n)):
        b=create_mock_board()
        winrate=sim_runs(b,400)
        if winrate>0.45:
            print(b.players[0].hand)
        winrates.append(winrate)

    fig, ax = plt.subplots()

    ax.hist(winrates, bins=50, linewidth=0.5, edgecolor="white")


    plt.show()








