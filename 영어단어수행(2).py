import random

import time

from collections import deque

import os
 
# ---------------------------------------------------------

# 단어 데이터 (총 81개)

# ---------------------------------------------------------

# ---------------------------------------------------------

# 단어 데이터

# ---------------------------------------------------------

vocab_data = [

    # Chapter 29

    {"word": "unbearably", "def_en": "", "synonyms": "intolerably, insufferably, extremely", "antonyms": "", "passage": "The air became [ BLANK ] humid. Stanley was drenched in sweat."},

    {"word": "formation", "def_en": "", "synonyms": "arrangement, structure, organization", "antonyms": "", "passage": "In that split second Stanley thought he saw an unusual rock [ BLANK ] on top of one of the mountain peaks."},

    {"word": "delirious", "def_en": "", "synonyms": "confused, disoriented, incoherent", "antonyms": "", "passage": "No one ever knew what he meant by that. He was [ BLANK ] when he said it."},
 
    # Chapter 30

    {"word": "deprive", "def_en": "", "synonyms": "deny, rob, strip", "antonyms": "", "passage": "Mr. Sir was no longer [ BLANK ]ing him of water. After having to get by on less water for a week or so, Stanley now felt like he had all the water he could want."},

    {"word": "make out", "def_en": "", "synonyms": "distinguish, pick out, catch sight of", "antonyms": "", "passage": "He thought he could [ BLANK ] a spot where the top of one mountain seemed to jut upward, but it didn't seem very impressive."},

    {"word": "feeble", "def_en": "very weak", "synonyms": "", "antonyms": "", "passage": "Stanley made a [ BLANK ] attempt to punch Zigzag, then he felt a flurry of fists against his head and neck."},

    {"word": "strangle", "def_en": "to kill or hurt someone by squeezing their neck so they cannot breathe", "synonyms": "", "antonyms": "", "passage": "\"There was a riot,\" Mr. Pendanski told her. \"Zero almost [ BLANK ]d Ricky.\""},

    {"word": "uneasily", "def_en": "", "synonyms": "nervously, anxiously, uncomfortably", "antonyms": "", "passage": "\"Well then, tell me, what does c-a-t spell?\" Zero glanced around [ BLANK ]."},

    {"word": "have it in for", "def_en": "to not like somebody and be unpleasant to them", "synonyms": "", "antonyms": "", "passage": "Stanley didn't know why Mr. Pendanski seemed to [ BLANK ] Zero."},
 
    # Chapter 31

    {"word": "keep an eye out", "def_en": "to look for somebody/something while you are doing other things", "synonyms": "", "antonyms": "", "passage": "He [ BLANK ] for Zero, but Zero didn't come back."},

    {"word": "convince", "def_en": "to make somebody/yourself believe that something is true", "synonyms": "", "antonyms": "", "passage": "He tried to [ BLANK ] himself it wasn't impossible."},
 
    # Chapter 32

    {"word": "fidget", "def_en": "to make small movements, especially because you are nervous or bored", "synonyms": "", "antonyms": "", "passage": "Two days later a new kid was assigned to Group D. His name was Brian, but X-Ray called him Twitch because he was always [ BLANK ]ing."},

    {"word": "break into", "def_en": "to enter a building by force; to open a car, etc. by force", "synonyms": "", "antonyms": "", "passage": "He claimed he could [ BLANK ] a car, disconnect the alarm, and hot-wire the engine, all in less than a minute."},

    {"word": "dangle", "def_en": "to hang or swing loosely in the air", "synonyms": "", "antonyms": "", "passage": "He looked through the window. The keys were there, [ BLANK ]ing in the ignition."},

    {"word": "lurch", "def_en": "to make a sudden, unsteady movement forward or to one side", "synonyms": "stagger, reel, pitch", "antonyms": "", "passage": "The gear shift was on the floor next to the seat... The truck [ BLANK ]ed forward."},

    {"word": "lopsided", "def_en": "having one side lower, smaller, etc. than the other", "synonyms": "", "antonyms": "", "passage": "He had driven straight into a hole. He lay on the dirt staring at the truck, which stuck [ BLANK ] into the ground."},
 
    # Chapter 33

    {"word": "cluster", "def_en": "", "synonyms": "bunch, clump, mass", "antonyms": "", "passage": "Just when he thought he'd passed the last hole, he'd come across another [ BLANK ] of them, a little farther away."},
 
    # Chapter 34

    {"word": "mirage", "def_en": "an image that looks real, especially in a hot place, but is not actually there", "synonyms": "", "antonyms": "", "passage": "There wasn't any water. It was a [ BLANK ] caused by the shimmering waves of heat rising off the dry ground."},

    {"word": "come into view", "def_en": "to suddenly emerge or become visible", "synonyms": "", "antonyms": "", "passage": "At first he wasn't sure if this was another kind of mirage, but the farther he walked, the clearer they [ BLANK ]."},

    {"word": "grimly", "def_en": "in a very serious, gloomy, or depressing manner", "synonyms": "", "antonyms": "", "passage": "Someone may have drowned here, he thought [ BLANK ]— at the same spot where he could very well die of thirst."},
 
    # Chapter 35

    {"word": "drooping", "def_en": "hanging down (as from exhaustion or weakness)", "synonyms": "", "antonyms": "", "passage": "Zero's face looked like a jack-o'-lantern that had been left out too many days past Halloween— half rotten, with sunken eyes and a [ BLANK ] smile."},

    {"word": "raspy", "def_en": "(of somebody’s voice) having a rough sound, as if the person has a sore throat", "synonyms": "", "antonyms": "", "passage": "\"Is that water?\" Zero asked. His voice was weak and [ BLANK ]."},

    {"word": "scatter", "def_en": "to throw or drop things in different directions so that they cover an area of ground", "synonyms": "", "antonyms": "", "passage": "There were enough cracks and holes in the bottom of the boat, now the roof, to provide light and ventilation. He could see empty jars [ BLANK ]ed about."},

    {"word": "jagged", "def_en": "with rough, pointed, often sharp edges", "synonyms": "", "antonyms": "", "passage": "He quickly brought the jar to his mouth and licked the sploosh off the [ BLANK ] edges before it spilled."},
 
    # Chapter 36

    {"word": "fraction", "def_en": "a small part or amount of something", "synonyms": "", "antonyms": "", "passage": "Zero collapsed. The shovel stayed up a [ BLANK ] of a second longer, perfectly balanced on the tip of the blade, then it fell next to him."},

    {"word": "slope", "def_en": "(of a horizontal surface) to be at an angle so that it is higher at one end than the other", "synonyms": "", "antonyms": "", "passage": "Unlike the eastern shore, where Camp Green Lake was situated, the western shore did not [ BLANK ] down gradually."},

    {"word": "gradually", "def_en": "slowly, over a long period of time, little by little", "synonyms": "", "antonyms": "", "passage": "Huge white stone cliffs rose up before them. Unlike the eastern shore, where Camp Green Lake was situated, the western shore did not slope down [ BLANK ]."},

    {"word": "crisscross", "def_en": "to make a pattern on something with many straight lines that cross each other", "synonyms": "", "antonyms": "", "passage": "Stanley still managed to hold the sack of jars in his left hand as he slowly moved up, from ledge to ledge, [ BLANK ]ing the rut."},

    {"word": "tremble", "def_en": "to shake", "synonyms": "quiver, shiver, shudder", "antonyms": "", "passage": "Zero stayed with him, somehow. His frail body [ BLANK ]d terribly as he climbed the stone wall."},

    {"word": "interweave", "def_en": "to twist together two or more pieces of thread, wool, etc.", "synonyms": "", "antonyms": "", "passage": "Stanley cupped his hands together, and Zero stepped on his [ BLANK ]n fingers."},

    {"word": "protrude", "def_en": "to stick out from a place or a surface", "synonyms": "", "antonyms": "", "passage": "He was able to lift Zero high enough for him to grab the [ BLANK ]ing slab of rock."},
 
    # Chapter 37

    {"word": "increment", "def_en": "a regular increase, addition", "synonyms": "", "antonyms": "", "passage": "It became too steep to go straight up. Instead they zigzagged back and forth, increasing their altitude by small [ BLANK ]s every time they changed directions."},

    {"word": "attract", "def_en": "to make someone interested in something so that they come to see or hear it, draw, entice, allure", "synonyms": "", "antonyms": "", "passage": "A swarm of gnats hovered around them, [ BLANK ]ed by their sweat. Neither Stanley nor Zero had the strength to try to swat at them."},

    {"word": "wrenching", "def_en": "causing great physical or mental suffering", "synonyms": "agonizing, tormenting, torturing", "antonyms": "", "passage": "Zero made a horrible, [ BLANK ] noise as he doubled over and grabbed his stomach."},

    {"word": "tangle", "def_en": "to twist something into an untidy mass; to become twisted in this way", "synonyms": "", "antonyms": "", "passage": "As they climbed higher, the patches of weeds grew thicker, and they had to be careful not to get their feet [ BLANK ]d in thorny vines."},
 
    # Chapter 38

    {"word": "upright", "def_en": "not lying down, and with the back straight", "synonyms": "", "antonyms": "", "passage": "Stanley took hold of Zero's forearms and pulled him [ BLANK ]."},

    {"word": "resemble", "def_en": "to look like or be similar to another person or thing", "synonyms": "", "antonyms": "", "passage": "It seemed to grow bigger with each step he took. It no longer [ BLANK ]d a thumb."},

    {"word": "tumble", "def_en": "to fall downwards, often hitting the ground several times", "synonyms": "", "antonyms": "", "passage": "Zero's head knocked against the back of his shoulder as he fell and [ BLANK ]d into a small muddy gully."},

    {"word": "come across", "def_en": "to meet somebody by chance", "synonyms": "", "antonyms": "", "passage": "But I don't want to [ BLANK ] one of those red-eyed monsters. I seen one once, and that was enough."},

    {"word": "comprehend", "def_en": "to understand something fully", "synonyms": "", "antonyms": "", "passage": "It took a moment for Stanley to [ BLANK ]. \"Clyde Livingston's shoes?\""},
 
    # Chapter 39~40

    {"word": "intertwine", "def_en": "to twist things together; to closely connect something with something else", "synonyms": "", "antonyms": "", "passage": "He [ BLANK ]d his fingers and tried to rub out the pain."},

    {"word": "contritely", "def_en": "in a way that shows that you are very sorry for something bad that you have done", "synonyms": "", "antonyms": "", "passage": "\"I'm glad Becca's all right,\" Hattie said [ BLANK ]."},

    {"word": "indentation", "def_en": "a cut, gap or mark in the edge or surface of something", "synonyms": "", "antonyms": "", "passage": "He saw a large [ BLANK ] in the weeds a little farther down the mountain."},
 
    # Chapter 41

    {"word": "murky", "def_en": "not clear; dark or dirty with mud or another substance", "synonyms": "", "antonyms": "", "passage": "It contained almost two feet of [ BLANK ] water."},

    {"word": "contaminate", "def_en": "to make a substance or place dirty by adding a substance that is dangerous or carries disease", "synonyms": "", "antonyms": "", "passage": "They didn't dip their socks into the hole, afraid to [ BLANK ] the water."},
 
    # Chapter 42

    {"word": "experience", "def_en": "to have a particular situation", "synonyms": "", "antonyms": "", "passage": "He wondered if perhaps he was [ BLANK ]ing something like that."},

    {"word": "flutter", "def_en": "to move lightly and quickly", "synonyms": "", "antonyms": "", "passage": "It stayed on Zero's face for an amazingly long time before [ BLANK ]ing off to the side."},

    {"word": "coincidence", "def_en": "the fact of two things happening at the same time by chance, in a surprising way", "synonyms": "", "antonyms": "", "passage": "It was more than a [ BLANK ]. It had to be destiny."},
 
    # Chapter 43

    {"word": "recapture", "def_en": "to experience again or regain a feeling, quality, or situation from the past", "synonyms": "", "antonyms": "", "passage": "Instead he tried to [ BLANK ] the feelings he'd had the night before— the inexplicable feeling of happiness, the sense of destiny."},

    {"word": "inexplicable", "def_en": "that cannot be understood or explained", "synonyms": "", "antonyms": "", "passage": "Instead he tried to recapture the feelings he'd had the night before— the [ BLANK ] feeling of happiness, the sense of destiny."},

    {"word": "indistinct", "def_en": "that cannot be seen, heard or remembered clearly", "synonyms": "", "antonyms": "", "passage": "They were still too far away to see the camp, but he could hear a blend of [ BLANK ] voices."},

    {"word": "distinctive", "def_en": "having a quality or characteristic that makes something different and easily noticed", "synonyms": "", "antonyms": "", "passage": "As they got closer he occasionally could hear Mr. Sir's [ BLANK ] bark."},
 
    # Chapter 44

    {"word": "pronounced", "def_en": "very obvious, easy to notice or strongly expressed", "synonyms": "", "antonyms": "", "passage": "As the dirt chipped and flaked away, the hard object became more [ BLANK ]."},

    {"word": "expose", "def_en": "to show something that is usually hidden", "synonyms": "", "antonyms": "", "passage": "He scraped at the dirt wall, until he [ BLANK ]d one entire side of the box-like object."},

    {"word": "budge", "def_en": "to move slightly; to make something/ somebody move slightly", "synonyms": "", "antonyms": "", "passage": "He tried pulling it out, but it wouldn't [ BLANK ]."},

    {"word": "precarious", "def_en": "not safe or certain; dangerous", "synonyms": "", "antonyms": "", "passage": "As his tunnel grew deeper and wider—and more [ BLANK ]."},
 
    # Chapter 45~46

    {"word": "in the nick (of time)", "def_en": "at the very last moment, just before it is too late", "synonyms": "", "antonyms": "", "passage": "\"You boys arrived just [ BLANK ]—\" the Warden started to say. She stopped talking and she stopped walking."},

    {"word": "commotion", "def_en": "", "synonyms": "disturbance, ruckus, uproar", "antonyms": "", "passage": "He wondered if he should try to scramble out of the hole before the lizards turned on him, but he didn't want to cause any [ BLANK ]."},

    {"word": "perch", "def_en": "to land and stay on a branch, etc.", "synonyms": "", "antonyms": "", "passage": "Stanley glanced at Zero. A lizard was [ BLANK ]ed on his shoulder. Zero remained perfectly still except for his right hand..."},

    {"word": "strenuous", "def_en": "needing great effort and energy", "synonyms": "", "antonyms": "", "passage": "His legs were sore from remaining rigid for so long. Standing still was more [ BLANK ] than walking."},
 
    # Chapter 47

    {"word": "exaggerate", "def_en": "", "synonyms": "overstate, inflate, stretch", "antonyms": "", "passage": "The Warden had dark circles under her eyes from lack of sleep, and lines across her forehead and face which seemed [ BLANK ]d in the stark morning light."},

    {"word": "momentarily", "def_en": "", "synonyms": "briefly, for a moment, for a short time", "antonyms": "", "passage": "He had never seen a tarantula before, but there was no doubt what it was. He was [ BLANK ] fascinated by it, as its big hairy body moved slowly and steadily along."},

    {"word": "file a charge", "def_en": "to officially accuse someone of a crime through legal action", "synonyms": "", "antonyms": "", "passage": "\"I'm telling you right now, if any harm comes to him, we will be [ BLANK ]s not only against Ms. Walker and Camp Green Lake but the entire state of Texas as well.\""},

    {"word": "authenticate", "def_en": "", "synonyms": "verify, validate, confirm", "antonyms": "", "passage": "\"She didn't have proper authorization,\" said the Warden. \"I had a court order!\" \"It was not [ BLANK ]d,\" the Warden said."},

    {"word": "legitimate", "def_en": "lawful, valid, or genuinely real", "synonyms": "", "antonyms": "", "passage": "\"I needed authentication from the Attorney General,\" said the Warden. \"How do I know it's [ BLANK ]?\""},

    {"word": "custody", "def_en": "the state of being kept, guarded, or legally cared for by someone", "synonyms": "", "antonyms": "", "passage": "\"The boys in my [ BLANK ] have proven themselves dangerous to society. Am I supposed to just turn them loose...\""},

    {"word": "hospitalize", "def_en": "to send somebody to a hospital for treatment", "synonyms": "", "antonyms": "", "passage": "\"Stanley has been [ BLANK ]d for the last few days,\" the Warden explained."},

    {"word": "rant and rave", "def_en": "to shout or complain angrily and wildly", "synonyms": "", "antonyms": "", "passage": "\"He's been suffering from hallucinations and delirium. [ BLANK ]ing. He was in no condition to leave.\""},

    {"word": "in view of", "def_en": "considering something", "synonyms": "", "antonyms": "", "passage": "If I press charges, Stanley might have to return to prison. Now I'm willing, [ BLANK ] all the circumstances, to—"},
 
    # Chapter 48

    {"word": "think straight", "def_en": "to think in a clear or logical way", "synonyms": "", "antonyms": "", "passage": "He was so tired he couldn't [ BLANK ]. He felt as if he was walking in a dream..."},

    {"word": "detainee", "def_en": "a person who is kept in prison, especially by the police or government", "synonyms": "", "antonyms": "", "passage": "\"He has to open it!\" said the Warden. \"I have the right to check the personal property of any of the [ BLANK ]s.\""},

    {"word": "jurisdiction", "def_en": "the authority that an official organization has to make legal decisions about somebody/something", "synonyms": "", "antonyms": "", "passage": "\"He is no longer under your [ BLANK ],\" said Stanley's lawyer."},

    {"word": "pursuant to", "def_en": "according to or following something, especially a rule or law", "synonyms": "", "antonyms": "", "passage": "\"There's nothing I can do for your friend,\" said Ms. Morengo. \"You are released [ BLANK ] an order from the judge.\""},

    {"word": "misplace", "def_en": "to put something in the wrong place or lose track of where it is", "synonyms": "", "antonyms": "", "passage": "Mr. Pendanski went into the office. He returned a few minutes later and announced the file was apparently [ BLANK ]d."},

    {"word": "outrage", "def_en": "to make somebody very shocked and angry", "synonyms": "", "antonyms": "", "passage": "The Attorney General was [ BLANK ]d. \"What kind of camp are you running here, Ms. Walker?\""},

    {"word": "incarcerate", "def_en": "to put someone in prison or jail.", "synonyms": "", "antonyms": "", "passage": "The Attorney General stared at her. \"He was obviously [ BLANK ]d for a reason.\""},
 
    # Chapter 49~50

    {"word": "eliminate", "def_en": "", "synonyms": "remove, eradicate, exclude", "antonyms": "", "passage": "\"No, he's still working on that,\" explained Ms. Morengo. \"But he invented a product that [ BLANK ]s foot odor.\""},

    {"word": "tedious", "def_en": "", "synonyms": "boring, monotonous, tiresome", "antonyms": "", "passage": "The reader probably still has some questions, but unfortunately, from here on in, the answers tend to be long and [ BLANK ]."},

    {"word": "count", "def_en": "", "synonyms": "matter, be important, carry weight", "antonyms": "", "passage": "The people at Stanley's house cheered, as if the run really [ BLANK ]ed."},

    {"word": "absent-mindedly", "def_en": "in a way that shows you are not paying attention to what you are doing", "synonyms": "", "antonyms": "", "passage": "A woman sitting in the chair behind Hector was [ BLANK ] fluffing his hair with her fingers."},

    {"word": "fluff", "def_en": "to shake or brush something so that it looks larger and/or softer", "synonyms": "", "antonyms": "", "passage": "A woman sitting in the chair behind Hector was absent-mindedly [ BLANK ]ing his hair with her fingers."}

]

# ---------------------------------------------------------

# 전역 설정 및 상태 변수

# ---------------------------------------------------------

unknown_words = []       # 모르는 단어를 저장할 리스트

auto_advance_delay = 0   # 0이면 수동(Enter), 0 이상이면 자동 대기 시간(초)

ask_add_mode = True      # 오답 시 목록 추가를 물어볼지 여부
 
def clear_screen():

    os.system('cls' if os.name == 'nt' else 'clear')
 
def handle_wait(delay):

    """설정된 시간에 따라 대기하거나 Enter 입력을 받습니다."""

    if delay == 0:

        input("\n계속하려면 Enter 키를 누르세요...")

    else:

        print(f"\n(... {delay}초 후 자동으로 넘어갑니다 ...)")

        time.sleep(delay)
 
def play_cycle(word_list, mode="standard", section_info="전체"):

    history = deque(maxlen=20)

    cycle_count = 1

    while True:

        cycle_wrong_words = []

        cycle_total_questions = len(word_list)

        cycle_correct_answers = 0

        current_list = list(word_list)

        random.shuffle(current_list)

        for index, item in enumerate(current_list, 1):

            clear_screen()

            if len(history) > 0:

                accuracy = (sum(history) / len(history)) * 100

            else:

                accuracy = 0.0

            if mode == "standard":

                mode_title = f"전체 단어 퀴즈 ({section_info})"

            else:

                mode_title = "모르는 단어 복습 퀴즈"

            print("=" * 60)

            print(f"📖 {mode_title} - 사이클 {cycle_count}")

            print("-" * 60)

            print(f"진행도: {index}/{len(current_list)} 단어 | 최근 20개 정답률: {accuracy:.1f}%")

            print("💡 (언제든 '0'을 입력하면 메인 메뉴로 돌아갑니다.)")

            print("-" * 60)

            target_word = item["word"]

            first_letter = target_word[0].lower()

            word_count = len(target_word.split())

            blank_str = " ".join(["[ _____ ]"] * word_count)

            passage = item["passage"].replace("[ BLANK ]", blank_str)

            print(f"🎯 첫 글자   | {first_letter}")

            if item["def_en"]:

                print(f"📖 영어 정의 | {item['def_en']}")

            if item["synonyms"]:

                print(f"🔗 유의어    | {item['synonyms']}")

            if item["antonyms"]:

                print(f"⛔ 반의어    | {item['antonyms']}")

            print(f"📝 예문      | {passage}")

            print("-" * 60)

            user_input = input("정답을 입력하세요: ").strip().lower()

            if user_input == '0':

                print("\n🏃 퀴즈를 중단하고 초기 메뉴로 돌아갑니다.")

                time.sleep(1)

                return

            if user_input == target_word.lower():

                print("\n✅ 정답입니다!")

                history.append(1)

                cycle_correct_answers += 1

                if mode == "unknown":

                    ans = input("모르는 단어 목록에서 제거하시겠습니까? (y/n): ").strip().lower()

                    if ans == 'y':

                        if item in unknown_words:

                            unknown_words.remove(item)

                        print("✨ 목록에서 제거되었습니다.")

                        time.sleep(0.5) 

                    else:

                        handle_wait(auto_advance_delay)

                else:

                    handle_wait(auto_advance_delay)

            else:

                print(f"\n❌ 틀렸습니다. 정답은 [ {target_word} ] 입니다.")

                history.append(0)

                cycle_wrong_words.append(item)

                if mode == "standard":

                    if ask_add_mode:

                        if item not in unknown_words:

                            ans = input("모르는 단어 목록에 추가하시겠습니까? (y/n): ").strip().lower()

                            if ans == 'y':

                                unknown_words.append(item)

                                print("📝 모르는 단어 목록에 추가되었습니다.")

                            time.sleep(0.5)

                        else:

                            print("📌 (이미 모르는 단어 목록에 있는 단어입니다.)")

                            handle_wait(auto_advance_delay)

                    else:

                        handle_wait(auto_advance_delay)

                else:

                    handle_wait(auto_advance_delay)
 
        clear_screen()

        cycle_accuracy = (cycle_correct_answers / cycle_total_questions) * 100 if cycle_total_questions > 0 else 0

        print("=" * 60)

        print(f"🎉 사이클 {cycle_count} 완료 요약")

        print("=" * 60)

        print(f"🎯 이번 사이클 최종 정답률 : {cycle_accuracy:.1f}% ({cycle_correct_answers}/{cycle_total_questions})")

        print("-" * 60)

        if cycle_wrong_words:

            print("📝 틀린 단어 목록:")

            for w in cycle_wrong_words:

                desc = w["synonyms"] if w["synonyms"] else w["def_en"]

                print(f"  - {w['word']}: {desc}")

        else:

            print("🌟 완벽합니다! 이번 사이클에서 틀린 단어가 하나도 없습니다.")

        print("-" * 60)

        if mode == "unknown" and len(unknown_words) == 0:

            print("대단해요! 모르는 단어 목록을 마스터했습니다. 메뉴로 돌아갑니다.")

            time.sleep(2)

            return

        user_input = input("다음 사이클을 시작하려면 Enter, 메뉴로 가려면 '0'을 입력: ").strip().lower()

        if user_input == '0':

            return

        cycle_count += 1
 
def settings_menu():

    global auto_advance_delay

    while True:

        clear_screen()

        print("=" * 40)

        print("⏳ 화면 자동 전환 시간 설정")

        print("=" * 40)

        print("1. 0.1초 (즉시)")

        print("2. 0.5초")

        print("3. 1.0초")

        print("4. 1.5초")

        print("5. 2.0초")

        print("6. 수동 (Enter 키 눌러 넘기기)")

        print("0. 뒤로 가기")

        print("-" * 40)

        current_status = "수동 (Enter)" if auto_advance_delay == 0 else f"{auto_advance_delay}초"

        print(f"▶ 현재 설정: {current_status}")

        choice = input("\n원하는 번호를 선택하세요: ").strip().lower()

        if choice == '1': auto_advance_delay = 0.1

        elif choice == '2': auto_advance_delay = 0.5

        elif choice == '3': auto_advance_delay = 1.0

        elif choice == '4': auto_advance_delay = 1.5

        elif choice == '5': auto_advance_delay = 2.0

        elif choice == '6': auto_advance_delay = 0

        elif choice == '0': return

        else:

            print("잘못된 입력입니다.")

            time.sleep(1)
 
def section_quiz_setup():

    """원하는 구간(시작 번호 ~ 끝 번호) 퀴즈 설정"""

    total_words = len(vocab_data)

    while True:

        clear_screen()

        print("=" * 50)

        print("📖 원하는 구간만 퀴즈 시작")

        print("=" * 50)

        print(f"현재 총 {total_words}개의 단어가 있습니다.")

        print("학습할 단어의 시작 번호와 끝 번호를 설정합니다.")

        print("0. 뒤로 가기")

        print("-" * 50)

        start_input = input(f"시작 번호를 입력하세요 (1~{total_words}): ").strip()

        if start_input == '0':

            return

        if not start_input.isdigit() or not (1 <= int(start_input) <= total_words):

            print(f"\n1에서 {total_words} 사이의 숫자를 입력해주세요.")

            time.sleep(1.5)

            continue

        end_input = input(f"끝 번호를 입력하세요 ({start_input}~{total_words}): ").strip()

        if end_input == '0':

            return

        if not end_input.isdigit() or not (int(start_input) <= int(end_input) <= total_words):

            print(f"\n{start_input}에서 {total_words} 사이의 숫자를 입력해주세요.")

            time.sleep(1.5)

            continue

        start_idx = int(start_input)

        end_idx = int(end_input)

        selected_words = vocab_data[start_idx - 1 : end_idx]

        play_cycle(selected_words, mode="standard", section_info=f"{start_idx}번째~{end_idx}번째 단어")

        return
 
def main_menu():

    global ask_add_mode

    while True:

        clear_screen()

        print("=" * 50)

        print("🚀 Holes Vocabulary Quiz Master")

        print("=" * 50)

        print("1. 전체 단어 퀴즈 시작")

        print("2. 원하는 구간만 퀴즈 시작 (A번째 ~ B번째)")

        print(f"3. 모르는 단어 복습 시작 (현재: {len(unknown_words)}개)")

        print("4. 화면 전환 시간 설정")

        print(f"5. 오답 시 목록 추가 질문: [{'ON' if ask_add_mode else 'OFF'}]")

        print("0. 프로그램 종료")

        print("-" * 50)

        choice = input("메뉴를 선택하세요: ").strip().lower()

        if choice == '1':

            play_cycle(vocab_data, mode="standard", section_info="전체")

        elif choice == '2':

            section_quiz_setup()

        elif choice == '3':

            if len(unknown_words) == 0:

                print("\n모르는 단어가 없습니다!")

                time.sleep(1.5)

            else:

                play_cycle(unknown_words, mode="unknown")

        elif choice == '4':

            settings_menu()

        elif choice == '5':

            ask_add_mode = not ask_add_mode

            print(f"\n오답 질문 모드가 {'켜졌' if ask_add_mode else '꺼졌'}습니다.")

            time.sleep(1)

        elif choice == '0':

            print("\n프로그램을 종료합니다. 열공하세요! 👍")

            break

        else:

            print("\n잘못된 입력입니다.")

            time.sleep(1)
 
if __name__ == "__main__":

    main_menu()
 