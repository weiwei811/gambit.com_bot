from itertools import combinations

# [13,"s"]
# spade
# diamond
# heart
# clubs

def classify_5(cards):
    # print(cards)
    card_suits = [card[1] for card in cards]
    card_nums = [card[0] for card in cards]


    # 數字排序
    card_nums_sorted = sorted(card_nums)
    num_counts = {num: card_nums.count(num) for num in set(card_nums)}

    is_flush = (len(set(card_suits)) == 1)
    is_straight = False
    is_royalflush=False

    if len(set(card_nums_sorted)) == 5:
        if max(card_nums) - min(card_nums) == 4:
            is_straight = True
        elif set(card_nums_sorted) == {10,11,12,13,1}:
            if is_flush:
                is_royalflush = True
            else:
                is_straight = True

    if is_royalflush :
        return  10,1
    elif is_flush and is_straight:
        return 9,max(card_nums)
    elif 4 in num_counts.values():
        for num,count in num_counts.items():
            if count==4:
                four=num
        return 8,four
    elif 3 in num_counts.values() and 2 in num_counts.values():
        for num,count in num_counts.items():
            if count==3:
                three=num
        return 7,three
    elif is_flush:
        return 6,max(card_nums)
    elif is_straight:
        if set(card_nums)=={10,11,12,13,1}:
            return 5,1
        else:
            return 5,max(card_nums)
    elif 3 in num_counts.values():
        for num,count in num_counts.items():
            if count==3:
                three=num
        return 4,three
    elif list(num_counts.values()).count(2) == 2:
        two=[]
        for num,count in num_counts.items():
            if count==2:
                two.append(num)
        if 1 in two:
            return 3,1
        else:
            return 3,max(two)
    elif 2 in num_counts.values():
        for num,count in num_counts.items():
            if count==2:
                two=num
        return 2,two
    if 1 in set(card_nums):
        return 1,1
    else:
        return 1,max(card_nums)

def classify_hand(cards7):
    maxcombo=0
    print(cards7)
    for cards in combinations(cards7,5):
        combo_type,bigcard=classify_5(cards)
        if maxcombo<combo_type:
            maxcombo=combo_type
            maxcard=bigcard
    return maxcombo,maxcard

