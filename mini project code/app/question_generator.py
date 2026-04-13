# # import random
# # import json

# # with open("data/questions.json") as f:
# #     questions = json.load(f)


# # def generate_test():

# #     test = []

# #     # Logical
# #     for sub in questions["logical"]:
# #         test.append(random.choice(questions["logical"][sub]))

# #     # Mathematical
# #     for sub in questions["math"]:
# #         test.append(random.choice(questions["math"][sub]))

# #     # Verbal
# #     for sub in questions["verbal"]:
# #         test.append(random.choice(questions["verbal"][sub]))

# #     # Memory
# #     for sub in questions["memory"]:
# #         test.append(random.choice(questions["memory"][sub]))

# #     random.shuffle(test)

# #     return test

# # import random
# # import json

# # with open("data/questions.json") as f:
# #     questions = json.load(f)


# # def generate_test():

# #     test = []

# #     # Logical (5)
# #     logical_pool = []
# #     for sub in questions["logical"]:
# #         logical_pool.extend(questions["logical"][sub])
# #     test.extend(random.sample(logical_pool, 5))

# #     # Math (5)
# #     math_pool = []
# #     for sub in questions["math"]:
# #         math_pool.extend(questions["math"][sub])
# #     test.extend(random.sample(math_pool, 5))

# #     # Verbal (5)
# #     verbal_pool = []
# #     for sub in questions["verbal"]:
# #         verbal_pool.extend(questions["verbal"][sub])
# #     test.extend(random.sample(verbal_pool, 5))

# #     # Memory (5)
# #     memory_pool = []
# #     for sub in questions["memory"]:
# #         memory_pool.extend(questions["memory"][sub])
# #     test.extend(random.sample(memory_pool, 5))

# #     random.shuffle(test)

# #     return test

# import random
# import json
# import streamlit as st
# import time
# from pathlib import Path


# # ---------------- LOAD QUESTIONS ----------------

# PROJECT_ROOT = Path(__file__).resolve().parents[1]
# QUESTIONS_PATH = PROJECT_ROOT / "data" / "questions.json"

# with QUESTIONS_PATH.open(encoding="utf-8-sig") as f:
#     questions = json.load(f)


# def _flatten_domain_pool(value):
#     if isinstance(value, list):
#         return value
#     if isinstance(value, dict):
#         pool = []
#         for item in value.values():
#             if isinstance(item, list):
#                 pool.extend(item)
#         return pool
#     return []


# def _first_non_empty_domain(raw_questions, aliases):
#     for key in aliases:
#         if key in raw_questions:
#             pool = _flatten_domain_pool(raw_questions[key])
#             if pool:
#                 return pool
#     return []


# def _normalize_question_entry(entry):
#     if not isinstance(entry, dict):
#         return entry

#     normalized = dict(entry)
#     options = normalized.get("options")

#     # Convert keyed options (A/B/C...) into list options expected by the UI.
#     if isinstance(options, dict):
#         keyed_options = options
#         normalized["options"] = list(keyed_options.values())
#         answer = normalized.get("answer")
#         if isinstance(answer, str) and answer in keyed_options:
#             normalized["answer"] = keyed_options[answer]

#     return normalized


# def _sample_up_to(pool, count):
#     if not pool:
#         return []
#     return random.sample(pool, min(count, len(pool)))


# def _sample_exact(pool, count):
#     if not pool or count <= 0:
#         return []
#     if len(pool) >= count:
#         return random.sample(pool, count)
#     # If a domain has fewer unique questions than required, allow repeats.
#     return random.choices(pool, k=count)


# def _is_image_question(question):
#     return isinstance(question, dict) and bool(question.get("image"))


# def _question_identity(question):
#     if not isinstance(question, dict):
#         return str(question)
#     qid = question.get("id")
#     qtype = str(question.get("type", ""))
#     if qid is not None:
#         return f"id:{qtype}:{qid}"
#     return f"q:{qtype}:{question.get('question', '')}"


# def _deduplicate_questions(pool):
#     seen = set()
#     deduped = []
#     for q in pool:
#         key = _question_identity(q)
#         if key in seen:
#             continue
#         seen.add(key)
#         deduped.append(q)
#     return deduped


# def _select_domain_questions(pool, count, used_keys=None, require_image=True):
#     used_keys = used_keys or set()
#     available = [q for q in _deduplicate_questions(pool) if _question_identity(q) not in used_keys]

#     if not available:
#         return []

#     selected = []
#     image_questions = [q for q in available if _is_image_question(q)]

#     if require_image and image_questions:
#         img_q = random.choice(image_questions)
#         selected.append(img_q)

#     remaining = [q for q in available if q not in selected]
#     need = max(0, count - len(selected))
#     if need:
#         selected.extend(random.sample(remaining, min(need, len(remaining))))

#     for q in selected:
#         used_keys.add(_question_identity(q))

#     return selected


# def _with_default_type(pool, default_type):
#     normalized = []
#     for q in pool:
#         if isinstance(q, dict) and not q.get("type"):
#             cloned = dict(q)
#             cloned["type"] = default_type
#             normalized.append(cloned)
#         else:
#             normalized.append(q)
#     return normalized


# def _enforce_min_image_questions(test, all_domains, minimum=3):
#     if minimum <= 0:
#         return test

#     current_image_count = sum(1 for q in test if _is_image_question(q))
#     if current_image_count >= minimum:
#         return test

#     current_ids = {id(q) for q in test}
#     image_pool = []
#     for pool in all_domains.values():
#         for q in pool:
#             if _is_image_question(q) and id(q) not in current_ids:
#                 image_pool.append(q)

#     random.shuffle(image_pool)

#     needed = minimum - current_image_count
#     for img_q in image_pool:
#         if needed <= 0:
#             break

#         replace_index = next((idx for idx, q in enumerate(test) if not _is_image_question(q)), None)
#         if replace_index is None:
#             break

#         test[replace_index] = img_q
#         needed -= 1

#     return test


# def _build_question_bank(raw_questions):
#     bank = {
#         "numerical_reasoning": _first_non_empty_domain(
#             raw_questions,
#             ["numerical_reasoning", "NUMERICAL ABILITY", "numerical_ability"],
#         ),
#         "applied_reasoning": _first_non_empty_domain(
#             raw_questions,
#             ["applied_reasoning", "Applied reasoning", "applied reasoning"],
#         ),
#         "verbal_reasoning": _first_non_empty_domain(
#             raw_questions,
#             ["verbal_reasoning", "Verbal reasoning", "verbal"],
#         ),
#         "logical_reasoning": _first_non_empty_domain(
#             raw_questions,
#             ["logical_reasoning", "Logical reasoning", "LOGICAL REASONING", "logical"],
#         ),
#         "working_memory": _first_non_empty_domain(
#             raw_questions,
#             ["working_memory", "WORKING MEMORY", "memory"],
#         ),
#     }

#     for key, pool in bank.items():
#         bank[key] = [_normalize_question_entry(q) for q in pool if isinstance(q, dict)]

#     return bank


# questions = _build_question_bank(questions)


# def run_memory_display_countdown(state_key, seconds=5):
#     timer_key = f"{state_key}_timer_start"
#     if timer_key not in st.session_state:
#         st.session_state[timer_key] = time.time()

#     elapsed = int(time.time() - st.session_state[timer_key])
#     remaining = max(0, seconds - elapsed)

#     if remaining > 0:
#         unit = "second" if remaining == 1 else "seconds"
#         st.write(f"Time remaining: {remaining} {unit}")
#         time.sleep(1)
#         st.rerun()
#         return True

#     st.session_state.pop(timer_key, None)
#     return False


# # ---------------- GENERATE TEST ----------------

# def generate_test():
#     test = []
#     per_domain_count = 10
#     used_keys = set()

#     memory_supplemental = [
#         {"id": "MEM-DYN-1", "type": "number_memory"},
#         {"id": "MEM-DYN-2", "type": "word_memory"},
#         {"id": "MEM-DYN-3", "type": "image_memory"},
#         {"id": "MEM-DYN-4", "type": "grid_memory"},
#         {"id": "MEM-DYN-5", "type": "nback"},
#     ]

#     numerical_image_supplemental = [
#         {
#             "id": "NA-IMG-5",
#             "type": "NUMERICAL ABILITY",
#             "question": "What is the missing number that should replace the question mark?",
#             "image": "images/NA-5.png",
#             "options": {"A": "4", "B": "11", "C": "0", "D": "7", "E": "12", "F": "6"},
#             "answer": "C",
#         }
#     ]

#     logical_supplemental = [
#         {
#             "id": "LR-3",
#             "type": "LOGICAL REASONING",
#             "question": "Select the figure that follows the pattern.",
#             "image": "images/LR-3.png",
#             "options": {
#                 "A": "images/LR3-A.png",
#                 "B": "images/LR3-B.png",
#                 "C": "images/LR3-C.png",
#                 "D": "images/LR3-D.png",
#                 "E": "images/LR3-E.png",
#             },
#             "answer": "C",
#         },
#         {
#             "id": "LR-4",
#             "type": "LOGICAL REASONING",
#             "question": "Select a suitable option that would complete the series.",
#             "image": "images/LR-4.png",
#             "options": {
#                 "A": "images/LR4-A.png",
#                 "B": "images/LR4-B.png",
#                 "C": "images/LR4-C.png",
#                 "D": "images/LR4-D.png",
#             },
#             "answer": "C",
#         },
#         {
#             "id": "LR-5",
#             "type": "LOGICAL REASONING",
#             "question": "In the given figure, what is the total number of triangles?",
#             "image": "images/LR-5.png",
#             "options": {"A": "27", "B": "26", "C": "23", "D": "22"},
#             "answer": "C",
#         },
#         {
#             "id": "LR-6",
#             "type": "LOGICAL REASONING",
#             "question": "Consider the given three-dimensional figure, how many triangles does it have?",
#             "image": "images/LR-6.png",
#             "options": {"A": "18", "B": "20", "C": "22", "D": "24"},
#             "answer": "B",
#         },
#         {
#             "id": "LR-TEXT-1",
#             "type": "Logical reasoning",
#             "question": "Kevin, Joseph, and Nicholas are 3 brothers. Kevin is the oldest. Nicholas is not the oldest. Joseph is not the youngest. Who is the youngest?",
#             "options": ["Joseph", "Kevin", "Nicholas", "Both Joseph and Nicholas"],
#             "answer": "Nicholas",
#         },
#         {
#             "id": "LR-TEXT-2",
#             "type": "Logical reasoning",
#             "question": "Safe : Secure :: Protect : ?",
#             "options": ["Lock", "Guard", "Sure", "Conserve"],
#             "answer": "Guard",
#         },
#     ]

#     working_memory_supplemental = [
#         {
#             "id": "WM-1",
#             "type": "WORKING MEMORY",
#             "question": "Observe the image for 30 seconds. After it disappears, list all the objects you remember.",
#             "image": "images/WM-1.png",
#             "input_type": "text",
#         },
#         {
#             "id": "WM-2",
#             "type": "WORKING MEMORY",
#             "question": "Based on your memory of Pattern A, identify the main change in Pattern B.",
#             "image": "images/WM-2.png",
#             "options": {
#                 "A": "A shape has changed its color",
#                 "B": "A shape has changed its position",
#                 "C": "A shape has changed its shape type",
#                 "D": "No change has occurred",
#             },
#             "answer": "A",
#         },
#         {
#             "id": "WM-TEXT-1",
#             "type": "WORKING MEMORY",
#             "question": "K, D, L, C, B, A - what is 2 before B?",
#             "options": ["D", "L", "C", "K"],
#             "answer": "L",
#         },
#         {
#             "id": "WM-TEXT-2",
#             "type": "WORKING MEMORY",
#             "question": "3, 8, 2, 9, 5 - reverse order",
#             "options": ["5, 9, 2, 8, 3", "3, 8, 2, 9, 5", "5, 2, 9, 8, 3", "9, 5, 2, 8, 3"],
#             "answer": "5, 9, 2, 8, 3",
#         },
#         {
#             "id": "WM-TEXT-3",
#             "type": "WORKING MEMORY",
#             "question": "Plants grow due to?",
#             "options": ["Water", "Sunlight", "Soil", "Air"],
#             "answer": "Sunlight",
#         },
#     ]

#     domain_pools = {
#         "numerical_reasoning": _with_default_type(
#             questions["numerical_reasoning"] + numerical_image_supplemental,
#             "NUMERICAL ABILITY",
#         ),
#         "applied_reasoning": _with_default_type(questions["applied_reasoning"], "Applied reasoning"),
#         "verbal_reasoning": _with_default_type([
#             q for q in questions["verbal_reasoning"] if q.get("type") != "subjective"
#         ], "Verbal reasoning"),
#         "logical_reasoning": _with_default_type(
#             questions["logical_reasoning"] + logical_supplemental,
#             "Logical reasoning",
#         ),
#         "working_memory": _with_default_type(
#             questions.get("working_memory", []) + working_memory_supplemental + memory_supplemental,
#             "WORKING MEMORY",
#         ),
#     }

#     for pool in domain_pools.values():
#         selected = _select_domain_questions(
#             pool,
#             per_domain_count,
#             used_keys=used_keys,
#             require_image=True,
#         )
#         test.extend(selected)

#     random.shuffle(test)
#     return test


# # ---------------- NUMBER MEMORY ----------------

# def number_memory_test(question_id):

#     if f"numbers_{question_id}" not in st.session_state:
#         st.session_state[f"numbers_{question_id}"] = [random.randint(1,9) for _ in range(5)]
#         st.session_state[f"show_numbers_{question_id}"] = True

#     # STEP 1 — SHOW NUMBERS
#     if st.session_state[f"show_numbers_{question_id}"]:

#         st.write("Memorize these numbers")

#         # Render numbers as styled badges for consistent formatting
#         nums = st.session_state[f"numbers_{question_id}"]
#         html = "".join([f"<span class='num-badge'>{n}</span>" for n in nums])
#         st.markdown(f"<div style='margin:8px 0'>{html}</div>", unsafe_allow_html=True)

#         if run_memory_display_countdown(f"show_numbers_{question_id}", 5):
#             return

#         st.session_state[f"show_numbers_{question_id}"] = False
#         st.rerun()

#     # STEP 2 — USER INPUT
#     else:

#         answer = st.text_input(
#             "Enter the numbers",
#             key=f"number_input_{question_id}"
#         )

#         if st.button("Submit Numbers", key=f"submit_numbers_{question_id}"):

#             st.session_state[f"user_answer_{question_id}"] = answer

#             st.success("Answer saved")


# # ---------------- WORD MEMORY ----------------

# def word_memory_test(question_id):

#     words = ["apple","tree","car","book","dog","pen","chair","phone"]

#     if f"memory_words_{question_id}" not in st.session_state:
#         st.session_state[f"memory_words_{question_id}"] = random.sample(words,4)
#         st.session_state[f"show_words_{question_id}"] = True

#     # STEP 1 — SHOW WORDS
#     if st.session_state[f"show_words_{question_id}"]:

#         st.write("Memorize these words")

#         for w in st.session_state[f"memory_words_{question_id}"]:
#             st.write(f"**{w}**")

#         if run_memory_display_countdown(f"show_words_{question_id}", 5):
#             return

#         st.session_state[f"show_words_{question_id}"] = False
#         st.rerun()

#     # STEP 2 — USER RECALL
#     else:

#         answer = st.text_input(
#             "Enter the words separated by space",
#             key=f"word_input_{question_id}"
#         )

#         if st.button("Submit Words", key=f"submit_word_{question_id}"):

#             # store answer only (no evaluation)
#             st.session_state[f"user_answer_{question_id}"] = answer

#             st.success("Answer saved")


# # ---------------- IMAGE MEMORY ----------------

# def image_memory_test(question_id):

#     images = ["dog","car","apple","tree","cat"]

#     if f"shown_images_{question_id}" not in st.session_state:
#         st.session_state[f"shown_images_{question_id}"] = random.sample(images,3)
#         st.session_state[f"show_images_{question_id}"] = True

#     # STEP 1: SHOW IMAGES
#     if st.session_state[f"show_images_{question_id}"]:

#         st.write("Memorize these images")

#         images_dir = Path(__file__).resolve().parents[1] / "data" / "images"

#         for img in st.session_state[f"shown_images_{question_id}"]:
#             candidate_paths = [
#                 images_dir / f"{img}.jpeg",
#                 images_dir / f"{img}.jpg",
#                 images_dir / f"{img}.png",
#             ]
#             image_path = next((path for path in candidate_paths if path.exists()), None)

#             if image_path is not None:
#                 st.image(str(image_path), width=120)
#             else:
#                 st.markdown(f"**{img}**")

#         if run_memory_display_countdown(f"show_images_{question_id}", 5):
#             return

#         st.session_state[f"show_images_{question_id}"] = False
#         st.rerun()

#     # STEP 2: USER RECALL
#     else:

#         answer = st.text_input(
#             "Enter the image names in the same order (space separated)",
#             key=f"image_input_{question_id}"
#         )

#         if st.button("Submit Images", key=f"submit_images_{question_id}"):

#             st.session_state[f"user_answer_{question_id}"] = answer

#             st.success("Answer saved")


# # ---------------- N-BACK (IMAGE ORDER MEMORY) ----------------

# def nback_memory_test(question_id):

#     images = ["dog", "car", "apple", "tree", "cat"]

#     if f"nback_images_{question_id}" not in st.session_state:
#         st.session_state[f"nback_images_{question_id}"] = random.sample(images, 4)
#         st.session_state[f"show_nback_{question_id}"] = True

#     if st.session_state[f"show_nback_{question_id}"]:
#         st.write("Memorize these images in order")

#         images_dir = Path(__file__).resolve().parents[1] / "data" / "images"

#         for img in st.session_state[f"nback_images_{question_id}"]:
#             candidate_paths = [
#                 images_dir / f"{img}.jpeg",
#                 images_dir / f"{img}.jpg",
#                 images_dir / f"{img}.png",
#             ]
#             image_path = next((path for path in candidate_paths if path.exists()), None)

#             if image_path is not None:
#                 st.image(str(image_path), width=120)
#             else:
#                 st.markdown(f"**{img}**")

#         if run_memory_display_countdown(f"show_nback_{question_id}", 5):
#             return

#         st.session_state[f"show_nback_{question_id}"] = False
#         st.rerun()

#     else:
#         answer = st.text_input(
#             "Type the image names in displayed order (space separated)",
#             key=f"nback_input_{question_id}",
#         )

#         if st.button("Submit Sequence", key=f"submit_nback_{question_id}"):
#             st.session_state[f"user_answer_{question_id}"] = answer
#             st.success("Answer saved")


# # ---------------- GRID MEMORY ----------------

# def grid_memory_test(question_id):

#     grid_size = 3
#     total_cells = grid_size * grid_size

#     # Generate pattern
#     if f"grid_pattern_{question_id}" not in st.session_state:
#         st.session_state[f"grid_pattern_{question_id}"] = random.sample(range(total_cells), 3)
#         st.session_state[f"show_grid_{question_id}"] = True

#     # STEP 1 — SHOW GRID
#     if st.session_state[f"show_grid_{question_id}"]:

#         st.write("Memorize the highlighted cells")

#         for i in range(total_cells):

#             if i % grid_size == 0:
#                 cols = st.columns(grid_size)

#             symbol = "🟩" if i in st.session_state[f"grid_pattern_{question_id}"] else "⬜"
#             cols[i % grid_size].markdown(f"# {symbol}")

#         if run_memory_display_countdown(f"show_grid_{question_id}", 5):
#             return

#         st.session_state[f"show_grid_{question_id}"] = False
#         st.rerun()

#     # STEP 2 — USER SELECT
#     else:

#         st.write("Select the cells you remember")

#         if f"grid_answer_{question_id}" not in st.session_state:
#             st.session_state[f"grid_answer_{question_id}"] = []

#         selected_cells = set(st.session_state[f"grid_answer_{question_id}"])

#         for i in range(total_cells):

#             if i % grid_size == 0:
#                 cols = st.columns(grid_size)

#             symbol = "🟩" if i in selected_cells else "⬜"
#             if cols[i % grid_size].button(symbol, key=f"grid_cell_{question_id}_{i}"):

#                 if i in selected_cells:
#                     st.session_state[f"grid_answer_{question_id}"].remove(i)
#                 else:
#                     st.session_state[f"grid_answer_{question_id}"].append(i)
#                 st.rerun()

#         # SUBMIT BUTTON
#         if st.button("Submit Grid", key=f"submit_grid_{question_id}"):

#             st.session_state[f"user_answer_{question_id}"] = st.session_state[f"grid_answer_{question_id}"]

#             st.success("Grid answer saved")

# import json
# import streamlit as st
# import time
# from pathlib import Path
# import random

# # ---------------- LOAD QUESTIONS ----------------

# PROJECT_ROOT = Path(__file__).resolve().parents[1]
# QUESTIONS_PATH = PROJECT_ROOT / "data" / "questions.json"

# with QUESTIONS_PATH.open(encoding="utf-8-sig") as f:
#     questions = json.load(f)

# # ---------------- FLEXIBLE KEY MATCH ----------------

# def get_domain(questions, possible_keys):
#     for key in possible_keys:
#         if key in questions:
#             return questions[key]
#     return {}

# # ---------------- MEMORY TIMER ----------------

# def run_memory_display_countdown(state_key, seconds=5):
#     timer_key = f"{state_key}_timer_start"

#     if timer_key not in st.session_state:
#         st.session_state[timer_key] = time.time()

#     elapsed = int(time.time() - st.session_state[timer_key])
#     remaining = max(0, seconds - elapsed)

#     if remaining > 0:
#         st.write(f"Time remaining: {remaining} seconds")
#         time.sleep(1)
#         st.rerun()
#         return True

#     st.session_state.pop(timer_key, None)
#     return False

# # ---------------- MEMORY TESTS ----------------

# def number_memory_test(qid):
#     if f"num_{qid}" not in st.session_state:
#         st.session_state[f"num_{qid}"] = [random.randint(1, 9) for _ in range(5)]
#         st.session_state[f"show_{qid}"] = True

#     if st.session_state[f"show_{qid}"]:
#         st.write("Memorize these numbers:")
#         st.write(st.session_state[f"num_{qid}"])

#         if run_memory_display_countdown(f"show_{qid}"):
#             return

#         st.session_state[f"show_{qid}"] = False
#         st.rerun()
#     else:
#         st.text_input("Enter numbers", key=f"user_answer_{qid}")


# def word_memory_test(qid):
#     words = ["apple", "car", "dog", "tree", "pen"]

#     if f"words_{qid}" not in st.session_state:
#         st.session_state[f"words_{qid}"] = random.sample(words, 3)
#         st.session_state[f"show_{qid}"] = True

#     if st.session_state[f"show_{qid}"]:
#         st.write("Memorize these words:")
#         st.write(st.session_state[f"words_{qid}"])

#         if run_memory_display_countdown(f"show_{qid}"):
#             return

#         st.session_state[f"show_{qid}"] = False
#         st.rerun()
#     else:
#         st.text_input("Enter words", key=f"user_answer_{qid}")


# def image_memory_test(qid):
#     st.write("Image memory test")


# def grid_memory_test(qid):
#     st.write("Grid memory test")


# def nback_memory_test(qid):
#     st.write("N-back test")

# # ---------------- GENERATE TEST ----------------

# def generate_test(level="medium"):
#     test = []

#     domain_pools = {
#         "NUMERICAL ABILITY": get_domain(questions, [
#             "NUMERICAL ABILITY", "numerical_ability"
#         ]).get(level, []),

#         "LOGICAL REASONING": get_domain(questions, [
#             "LOGICAL REASONING", "Logical reasoning", "logical_reasoning"
#         ]).get(level, []),

#         "VERBAL REASONING": get_domain(questions, [
#             "VERBAL REASONING", "Verbal reasoning", "verbal_reasoning"
#         ]).get(level, []),

#         "APPLIED REASONING": get_domain(questions, [
#             "APPLIED REASONING", "Applied reasoning", "applied_reasoning"
#         ]).get(level, []),

#         "WORKING MEMORY": get_domain(questions, [
#             "WORKING MEMORY", "Working memory", "working_memory"
#         ]).get(level, []),
#     }

#     for pool in domain_pools.values():
#         test.extend(pool)

#     # MEMORY TASKS
#     if level == "medium":
#         test.extend([
#             {"id": "MEM-1", "type": "number_memory"},
#             {"id": "MEM-2", "type": "word_memory"},
#         ])
#     else:
#         test.extend([
#             {"id": "MEM-3", "type": "image_memory"},
#             {"id": "MEM-4", "type": "grid_memory"},
#             {"id": "MEM-5", "type": "nback"},
#         ])

#     return test

# # ---------------- SCORING ----------------

# def calculate_detailed_score(test):
#     total_score = 0
#     total_questions = 0
#     domain_scores = {}

#     for q in test:
#         if "answer" not in q:
#             continue

#         domain = q.get("type", "Unknown")
#         qid = q.get("id")

#         if domain not in domain_scores:
#             domain_scores[domain] = {"score": 0, "total": 0}

#         domain_scores[domain]["total"] += 1
#         total_questions += 1

#         user_ans = st.session_state.get(f"user_answer_{qid}")

#         if user_ans == q["answer"]:
#             domain_scores[domain]["score"] += 1
#             total_score += 1

#     return total_score, total_questions, domain_scores

# # ---------------- MAIN ----------------

# def run_test():

#     if "test_level" not in st.session_state:
#         st.session_state["test_level"] = "medium"

#     if "current_test" not in st.session_state:
#         st.session_state["current_test"] = generate_test("medium")

#     st.title("🧠 Cognitive Assessment Test")

#     for q in st.session_state["current_test"]:

#         qid = q.get("id")
#         qtype = q.get("type")

#         if q.get("question"):
#             st.write(f"### {q['question']}")

#         if q.get("image"):
#             st.image(q["image"], width=200)

#         # MEMORY
#         if qtype == "number_memory":
#             number_memory_test(qid)

#         elif qtype == "word_memory":
#             word_memory_test(qid)

#         elif qtype == "image_memory":
#             image_memory_test(qid)

#         elif qtype == "grid_memory":
#             grid_memory_test(qid)

#         elif qtype == "nback":
#             nback_memory_test(qid)

#         # NORMAL QUESTIONS
#         else:
#             if "options" in q:
#                 options = q["options"]

#                 if isinstance(options, dict):
#                     options = list(options.values())

#                 st.radio("Choose answer", options, key=f"user_answer_{qid}")
#             else:
#                 st.text_input("Your answer", key=f"user_answer_{qid}")

#     # SUBMIT
#     if st.button("Submit Test"):

#         score, total, domain_scores = calculate_detailed_score(
#             st.session_state["current_test"]
#         )

#         st.write(f"## 🧮 Total Score: {score}/{total}")

#         percentage = (score / total) * 100 if total > 0 else 0
#         st.write(f"### 📊 Percentage: {percentage:.2f}%")

#         st.markdown("---")

#         st.write("## 📌 Domain-wise Performance")

#         for domain, data in domain_scores.items():
#             d_score = data["score"]
#             d_total = data["total"]
#             percent = (d_score / d_total) * 100 if d_total > 0 else 0

#             st.write(f"**{domain}** → {d_score}/{d_total} ({percent:.2f}%)")

#         st.markdown("---")

#         # MEDIUM → HARD
#         if st.session_state["test_level"] == "medium":

#             if percentage >= 60:
#                 st.success("✅ Medium Passed! Hard Unlocked 🚀")

#                 st.session_state["test_level"] = "hard"
#                 st.session_state["current_test"] = generate_test("hard")

#                 st.rerun()

#             else:
#                 st.error("❌ You did not pass. Try again.")

#         else:
#             if percentage >= 70:
#                 st.success("🔥 Excellent Performance")
#             else:
#                 st.warning("👍 Good attempt")

# # ---------------- RUN ----------------

# if __name__ == "__main__":
#     run_test()


import json
import streamlit as st
import random
import time
from pathlib import Path

# ---------------- PATH SETUP ----------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data"
IMAGE_PATH = DATA_PATH / "images"

QUESTIONS_PATH = DATA_PATH / "questions.json"

with QUESTIONS_PATH.open(encoding="utf-8-sig") as f:
    questions = json.load(f)

# ---------------- SAFE DOMAIN FETCH ----------------

def get_domain(keys):
    for k in keys:
        if k in questions:
            return questions[k]
    return {}

# ---------------- RANDOM PICK ----------------

def pick_random(pool, count=10):
    if not pool:
        return []

    if len(pool) >= count:
        return random.sample(pool, count)

    return random.choices(pool, k=count)

# ---------------- WORKING MEMORY ----------------

def get_working_memory_questions(level):


        if level == "medium":
            return [
                {
                    "id": "WM-M1",
                    "type": "wm_numbers",
                    "question": "Memorize the numbers carefully"
                },
                {
                    "id": "WM-M2",
                    "type": "wm_sequence",
                    "question": "Memorize the words carefully"
                }
            ]

        else:
            return [
                {
                    "id": "WM-H1",
                    "type": "wm_image",
                    "question": "Observe the image carefully and recall objects"
                },
                {
                    "id": "WM-H2",
                    "type": "wm_pattern",
                    "question": "Identify the change between Pattern A and Pattern B"
                }
            ]

# ---------------- GENERATE TEST ----------------

def generate_test(test_type="foundation"):
    test = []

    level = "medium" if test_type == "foundation" else "hard"

    domains = {
        "NUMERICAL": get_domain(["NUMERICAL ABILITY"]).get(level, []),

    "LOGICAL": get_domain([
        "LOGICAL REASONING",
        "Logical reasoning",
        "logical_reasoning"
    ]).get(level, []),

    "VERBAL": get_domain([
        "VERBAL REASONING",
        "Verbal reasoning",
        "verbal_reasoning"
    ]).get(level, []),

    "APPLIED": get_domain([
        "APPLIED REASONING",
        "Applied reasoning",
        "applied_reasoning"
    ]).get(level, []),
    }

    for name, pool in domains.items():

        if not pool:
            st.error(f"{name} domain is empty ❌ CHECK JSON KEY")
            continue

        st.write(f"{name} → {len(pool)} questions found ✅")

        test.extend(pick_random(pool, 10))

    test.extend(get_working_memory_questions(level))

    random.shuffle(test)
    return test

# ---------------- TIMER ----------------

def countdown(key, sec=10):

    if f"{key}_start" not in st.session_state:
        st.session_state[f"{key}_start"] = time.time()

    elapsed = int(time.time() - st.session_state[f"{key}_start"])
    remain = max(0, sec - elapsed)

    if remain > 0:
        st.write(f"Time left: {remain}s")
        time.sleep(1)
        st.rerun()
        return True

    del st.session_state[f"{key}_start"]
    return False

# ---------------- MEMORY RENDER ----------------

def render_memory(q):

    # 🔴 WM-H1 → IMAGE RECALL
    if q["type"] == "wm_image":

        img_path ="memory/WM-1.png"

        if "wm1_done" not in st.session_state:
            st.write("Memorize this image")
            st.image(str(img_path), width=500)

            if countdown("wm1", 10):
                return

            st.session_state["wm1_done"] = True
            st.rerun()

        else:
            st.text_input("List objects you remember", key=q["id"])

    # 🔴 WM-H2 → PATTERN MEMORY
    elif q["type"] == "wm_pattern":

        img_A ="memory/WM-2A.png"
        img_B = "memory/WM-2B.png"

        if "pattern_seen" not in st.session_state:

            st.write("Memorize Pattern A")
            st.image(str(img_A), width=300)

            if countdown("pattern", 10):
                return

            st.session_state["pattern_seen"] = True
            st.rerun()

        else:
            st.write("Now observe Pattern B and answer")

            st.image(str(img_B), width=300)

            st.radio(
                "What changed?",
                [
                    "A shape has changed its color",
                    "A shape has changed its position",
                    "A shape has changed its shape type",
                    "No change has occurred"
                ],
                key=q["id"]
            )

    # MEDIUM MEMORY

    elif q["type"] == "wm_numbers":
        nums = [random.randint(1, 9) for _ in range(5)]
        st.write("Memorize:", nums)
        if countdown(q["id"], 5): return
        st.text_input("Enter numbers", key=q["id"])

    elif q["type"] == "wm_sequence":
        st.radio("Answer", ["D", "L", "C", "K"], key=q["id"])

# ---------------- SCORING ----------------

def calculate_score(test):

    score = 0
    total = 0
    domain = {}

    for q in test:

        if "answer" not in q:
            continue

        d = q.get("type", "unknown")

        if d not in domain:
            domain[d] = {"score": 0, "total": 0}

        domain[d]["total"] += 1
        total += 1

        if st.session_state.get(q["id"]) == q["answer"]:
            domain[d]["score"] += 1
            score += 1

    return score, total, domain

# ---------------- MAIN ----------------

def run():

    if "stage" not in st.session_state:
        st.session_state.stage = "foundation"

    if "questions" not in st.session_state:
        st.session_state.questions = generate_test("foundation")

    st.title("🧠 Cognitive Test")

    for q in st.session_state.questions:

        st.write("###", q.get("question", ""))

        if q.get("image"):
            st.image(q["image"])

        if q.get("type", "").startswith("wm"):
            render_memory(q)

        else:
            if "options" in q:
                opts = q["options"]
                if isinstance(opts, dict):
                    opts = list(opts.values())

                st.radio("Answer", opts, key=q["id"])
            else:
                st.text_input("Answer", key=q["id"])

    # ---------------- SUBMIT ----------------

    if st.button("Submit"):

        score, total, domain = calculate_score(st.session_state.questions)

        st.write(f"Score: {score}/{total}")

        if total > 0:
            st.write(f"Percentage: {(score/total)*100:.2f}%")

        st.write("### Domain-wise")

        for d in domain:
            st.write(f"{d} → {domain[d]['score']}/{domain[d]['total']}")

        # FLOW

        if st.session_state.stage == "foundation":

            if total > 0 and (score / total) >= 0.6:
                st.success("Foundation Passed → Advanced Unlocked")

                st.session_state.stage = "advanced"
                st.session_state.questions = generate_test("advanced")
                st.rerun()

            else:
                st.error("Retry Foundation")

        else:
            st.success("Test Completed 🎉")

# ---------------- RUN ----------------

if __name__ == "__main__":
    run()