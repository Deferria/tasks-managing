import gradio as gr
import json
import shutil
import random
import datetime

from typing import List, Dict, Any, Optional, Tuple, Callable

# IO
def load_from_file() -> List[Dict[str, Any]]:
    with open('tasks.json', 'r', encoding='utf-8') as f:
        tasks = json.load(f)
    gr.Info("已从 tasks.json 加载任务!")

    return tasks

def save_to_file(tasks: List[Dict[str, Any]]):
    with open('tasks.json', 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=4)

    datetime_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open('task_meta.json', 'w', encoding='utf-8') as f:
        json.dump({"last_saved": datetime_now}, f, ensure_ascii=False, indent=4)

    gr.Info("已保存到 `tasks.json`! 请刷新此页面...")
    return None

def save_file() -> None:
    shutil.copyfile('tasks.json', 'F:\\Lean\\dedicated\\Deferria.github.io\\public\\tasks.json')
    shutil.copyfile('task_meta.json', 'F:\\Lean\\dedicated\\Deferria.github.io\\public\\task_meta.json')
    gr.Info("已将 `tasks.json` 存档到公开目录.")

# parser
def parse_tasks_disp(tasks: List[Dict[str, Any]]) -> List[List[str]]:
    return [[task.get("course_name", "N/A"), task.get("assignment_name", "N/A"), task.get("due_at", "N/A"), task.get("zombie", False), task.get("complete", False)] for task in tasks]

def display(tasks: List[Dict[str, Any]], show_zombie: bool = False) -> Tuple[str, List[List[str]]]:
    disp_str = ""
    for i, task in enumerate(tasks):
        if not show_zombie and task.get("zombie", False):
            continue
        disp_str += f"{i}. {task.get('course_name', 'N/A')} - {task.get('assignment_name', 'N/A')} (Due: {task.get('due_at', 'N/A')})\n"
    
    return disp_str, parse_tasks_disp(tasks)

# utils
def get_value_by_index(cards: List[Dict[str, Any]], index: int, key: str) -> Any | None:
    try:
        return cards[index].get(key)
    except IndexError:
        return None
    
def get_explanation_by_index(cards: List[Dict[str, Any]], index: int) -> str:
    return get_value_by_index(cards, index, "explanation")

def get_info_by_index(cards: List[Dict[str, Any]], index: int) -> str:
    course_name = get_value_by_index(cards, index, "course_name") or "N/A"
    assignment_name = get_value_by_index(cards, index, "assignment_name") or "N/A"
    explanation = get_value_by_index(cards, index, "explanation") or "N/A"

    info = f"Course: {course_name}\n"
    info += f"Assignment: {assignment_name}\n"
    info += f"Explanation: {explanation}\n"

    return info

def randomize_ids() -> Tuple[int, int]:
    course_id = random.randint(1000000, 9999999)
    assignment_id = random.randint(1000000, 9999999)
    return course_id, assignment_id

# operations
def add_task(
        tasks: List[Dict[str, Any]], 
        course_name: str,
        assignment_name: str,
        assignment_group_name: Optional[str],
        course_id: Optional[int],
        assignment_id: Optional[int],
        due_at: Optional[str],
        unlock_at: Optional[str],
        lock_at: Optional[str],
        explanation: Optional[str],
        url: Optional[str]
    ) -> List[Dict[str, Any]]:
    tasks.append({
        "course_name": course_name,
        "assignment_group_name": assignment_group_name,
        "assignment_name": assignment_name,
        "course_id": course_id,
        "assignment_id": assignment_id,
        "due_at": due_at,
        "unlock_at": unlock_at,
        "lock_at": lock_at,
        "explanation": explanation,
        "from": "manual",
        "to": "notification",
        "url": url,
        "zombie": False,
        "complete": False
    })
    gr.Info("已添加新任务: {} - {} \n请重新加载以查看更新.".format(course_name, assignment_name))
    return tasks

def delete_task_by_index(tasks: List[Dict[str, Any]], index: int) -> List[Dict[str, Any]]:
    if 0 <= index < len(tasks):
        removed = tasks.pop(index)
        gr.Info("已删除任务: {} - {}".format(removed.get("course_name", "N/A"), removed.get("assignment_name", "N/A")))
    else:
        gr.Warning("无效的索引: {}".format(index))
    return tasks

def delete_task_by_id(tasks: List[Dict[str, Any]], assignment_id: int) -> List[Dict[str, Any]]:
    tasks = [task for task in tasks if task.get("assignment_id") != assignment_id]
    gr.Info("已删除任务 ID: {}".format(assignment_id))
    return tasks

def show_task_info(task: Dict[str, Any]) -> str:
    info = f"Course: {task.get('course_name', 'N/A')}\n"
    info += f"Assignment: {task.get('assignment_name', 'N/A')}\n"
    info += f"Due At: {task.get('due_at', 'N/A')}\n"
    info += f"Unlock At: {task.get('unlock_at', 'N/A')}\n"
    info += f"Lock At: {task.get('lock_at', 'N/A')}\n"
    info += f"Explanation: {task.get('explanation', 'N/A')}\n"
    info += f"URL: {task.get('url', 'N/A')}\n"
    return info

def mark_as_zombie(tasks: List[Dict[str, Any]], index: int) -> List[Dict[str, Any]]:
    if 0 <= index < len(tasks):
        tasks[index]['zombie'] = True
        gr.Info("已标记任务为僵尸: {} - {}".format(tasks[index].get("course_name", "N/A"), tasks[index].get("assignment_name", "N/A")))
    else:
        gr.Warning("无效的索引: {}".format(index))
    return tasks

def mark_as_complete(tasks: List[Dict[str, Any]], index: int) -> List[Dict[str, Any]]:
    if 0 <= index < len(tasks):
        tasks[index]['complete'] = True
        gr.Info("已标记任务为完成: {} - {}".format(tasks[index].get("course_name", "N/A"), tasks[index].get("assignment_name", "N/A")))
    else:
        gr.Warning("无效的索引: {}".format(index))
    return tasks

def add_explanation(tasks: List[Dict[str, Any]], index: int, explanation: str) -> List[Dict[str, Any]]:
    if 0 <= index < len(tasks):
        tasks[index]['explanation'] = explanation
        gr.Info("已添加/更新任务解释: {} - {}".format(tasks[index].get("course_name", "N/A"), tasks[index].get("assignment_name", "N/A")))
    else:
        gr.Warning("无效的索引: {}".format(index))
    return tasks

with gr.Blocks(title="Tasks Dashboard") as demo:
    gr.Markdown("# Tasks Dashboard Webui")
    t = gr.State(load_from_file())
    with gr.Row():
        load_btn = gr.Button("Load Tasks", variant="secondary")
        disp_btn = gr.Button("Display Tasks", variant="default")
        save_btn = gr.Button("Save All Changes to File...", variant="primary")
        pass_btn = gr.Button("Pass File", variant="huggingface")

    with gr.Row():
        with gr.Column(scale=1):
            task_list = gr.Dataframe(headers=["Course", "Assignment", "Due Date", "Zombie", "Complete"], datatype=["str", "str", "str", "bool", "bool"], interactive=False, show_row_numbers=True)
            show_zombie_checkbox = gr.Checkbox(label="Show Zombie Tasks", value=False)
            display_str = gr.Textbox(label="Tasks Display", lines=10, interactive=False)

        with gr.Column(scale=1):
            with gr.Tab("Add Task"):
                course_name = gr.Textbox(label="Course Name (Mandatory)")
                assignment_name = gr.Textbox(label="Assignment Name (Mandatory)")
                assignment_group_name = gr.Textbox(label="Assignment Group Name (optional)")
                with gr.Row():
                    course_id = gr.Number(label="Course ID (optional)")
                    assignment_id = gr.Number(label="Assignment ID (optional)")

                randomize_btn = gr.Button("Randomize", variant="secondary")
                randomize_btn.click(fn=randomize_ids, outputs=[course_id, assignment_id])
                
                due_at = gr.DateTime(label="Due At (optional)", type="string")
                with gr.Row():
                    unlock_at = gr.DateTime(label="Unlock At (optional)", type="string")
                    lock_at = gr.DateTime(label="Lock At (optional)", type="string")
                explanation = gr.Textbox(label="Lock Explanation (optional)", lines=4)
                url = gr.Textbox(label="URL (optional)")
                add_btn = gr.Button("Add Task", variant="stop")
                clear_btn = gr.ClearButton([course_name, assignment_name, assignment_group_name, course_id, assignment_id, due_at, unlock_at, lock_at, explanation, url], value="Clear All Fields", variant="secondary")

                add_btn.click(
                    fn=add_task, 
                    inputs=[t, course_name, assignment_name, assignment_group_name, course_id, assignment_id, due_at, unlock_at, lock_at, explanation, url], 
                    outputs=t
                )

            with gr.Tab("Delete Task"):
                gr.Markdown("### Delete by Index")
                delete_index = gr.Number(label="Task Index to Delete", precision=0)
                del_idx_btn = gr.Button("Delete by Index", variant="stop")

                gr.Markdown("### Delete by Assignment ID")
                delete_id = gr.Number(label="Assignment ID to Delete", precision=0)
                del_id_btn = gr.Button("Delete by Assignment ID", variant="stop")

                del_idx_btn.click(fn=delete_task_by_index, inputs=[t, delete_index], outputs=t)
                del_id_btn.click(fn=delete_task_by_id, inputs=[t, delete_id], outputs=t)

            with gr.Tab("Task Info"):
                task_index_info = gr.Number(label="Task Index to Show Info", precision=0)
                show_info_btn = gr.Button("Show Task Info", variant="secondary")
                task_info_display = gr.Textbox(label="Task Info", lines=10, interactive=False)

                def show_info_by_index(tasks: List[Dict[str, Any]], index: int) -> str:
                    if 0 <= index < len(tasks):
                        return show_task_info(tasks[index])
                    else:
                        return "Invalid index: {}".format(index)

                show_info_btn.click(fn=show_info_by_index, inputs=[t, task_index_info], outputs=task_info_display)

            with gr.Tab("Mark Task"):
                task_index_mark = gr.Number(label="Task Index to Mark", precision=0)
                task_index_mark_info = gr.Textbox(label="Current Task Info", lines=3, interactive=False)
                mark_zombie_btn = gr.Button("Mark as Zombie", variant="primary")
                mark_complete_btn = gr.Button("Mark as Complete", variant="huggingface")

                task_index_mark.change(fn=get_info_by_index, inputs=[t, task_index_mark], outputs=task_index_mark_info)  # Clear info on index change

                mark_zombie_btn.click(fn=mark_as_zombie, inputs=[t, task_index_mark], outputs=t)
                mark_complete_btn.click(fn=mark_as_complete, inputs=[t, task_index_mark], outputs=t)

            with gr.Tab("Add Explanation"):
                with gr.Row():
                    task_index_expl = gr.Number(label="Task Index to Add Explanation", precision=0)
                    get_explanation_btn = gr.Button("Get Current Explanation", variant="secondary")
                explanation_text = gr.Textbox(label="Explanation Text", lines=5)
                add_expl_btn = gr.Button("Add/Update Explanation", variant="secondary")

                task_index_expl.change(fn=get_explanation_by_index, inputs=[t, task_index_expl], outputs=explanation_text)
                add_expl_btn.click(fn=add_explanation, inputs=[t, task_index_expl, explanation_text], outputs=t)

    load_btn.click(fn=load_from_file, outputs=t)
    save_btn.click(fn=save_to_file, inputs=t)
    disp_btn.click(fn=display, outputs=[display_str, task_list], inputs=[t, show_zombie_checkbox])
    pass_btn.click(fn=save_file)

if __name__ == "__main__":
    demo.launch(
        share=False,
        server_port=7830,
    )