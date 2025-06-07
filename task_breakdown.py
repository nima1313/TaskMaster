#!/usr/bin/env python3
"""
Task Breakdown Application
A minimalistic web app that breaks down tasks into smaller subtasks using Gemini API
"""

import os
import json
import re
from flask import Flask, render_template_string, request, jsonify
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# HTML Template with embedded CSS and JavaScript
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Task Breakdown</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        .container {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 24px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
            width: 100%;
            max-width: 800px;
            padding: 40px;
            transition: all 0.3s ease;
        }

        .container:hover {
            transform: translateY(-2px);
            box-shadow: 0 25px 70px rgba(0, 0, 0, 0.15);
        }

        h1 {
            text-align: center;
            color: #2d3748;
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .subtitle {
            text-align: center;
            color: #718096;
            font-size: 1.1rem;
            margin-bottom: 40px;
        }

        .input-section {
            margin-bottom: 30px;
        }

        label {
            display: block;
            margin-bottom: 8px;
            color: #4a5568;
            font-weight: 600;
            font-size: 0.95rem;
        }

        textarea {
            width: 100%;
            padding: 20px;
            border: 2px solid #e2e8f0;
            border-radius: 16px;
            resize: vertical;
            min-height: 120px;
            font-size: 1rem;
            font-family: inherit;
            transition: all 0.3s ease;
            background: #f8fafc;
        }

        textarea:focus {
            outline: none;
            border-color: #667eea;
            background: white;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .button-container {
            text-align: center;
            margin-bottom: 40px;
        }

        .btn {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 16px 32px;
            border-radius: 16px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 35px rgba(102, 126, 234, 0.4);
        }

        .btn:active {
            transform: translateY(0);
        }

        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        .loading {
            display: none;
            text-align: center;
            margin: 20px 0;
            color: #667eea;
            font-weight: 500;
        }

        .loading.show {
            display: block;
        }

        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid #e2e8f0;
            border-radius: 50%;
            border-top-color: #667eea;
            animation: spin 1s ease-in-out infinite;
            margin-right: 10px;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .result {
            display: none;
            margin-top: 30px;
        }

        .result.show {
            display: block;
            animation: fadeInUp 0.5s ease;
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .task-title {
            font-size: 1.4rem;
            font-weight: 700;
            color: #2d3748;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e2e8f0;
        }

        .checklist {
            list-style: none;
        }

        .checklist-item {
            display: flex;
            align-items: flex-start;
            margin-bottom: 16px;
            padding: 16px;
            background: #f8fafc;
            border-radius: 12px;
            border-left: 4px solid #667eea;
            transition: all 0.3s ease;
            position: relative;
            cursor: grab;
        }

        .checklist-item:hover {
            background: #f1f5f9;
            transform: translateX(4px);
        }

        .checklist-item:hover .task-actions {
            opacity: 1;
        }

        .checklist-item.dragging {
            opacity: 0.5;
            transform: rotate(5deg);
            cursor: grabbing;
            z-index: 1000;
        }

        .checklist-item.drag-over {
            border-top: 3px solid #667eea;
            background: #e6f3ff;
        }

        .drag-handle {
            margin-right: 12px;
            color: #cbd5e0;
            cursor: grab;
            font-size: 1.2rem;
            transition: color 0.3s ease;
        }

        .drag-handle:hover {
            color: #667eea;
        }

        .checklist-item input[type="checkbox"] {
            margin-right: 15px;
            width: 20px;
            height: 20px;
            cursor: pointer;
            accent-color: #667eea;
        }

        .checklist-item label {
            flex: 1;
            margin-bottom: 0;
            cursor: pointer;
            font-weight: 500;
            line-height: 1.4;
        }

        .checklist-item.completed {
            opacity: 0.7;
            background: #e6fffa;
            border-left-color: #38b2ac;
        }

        .checklist-item.completed label {
            text-decoration: line-through;
            color: #718096;
        }

        .task-actions {
            opacity: 0;
            transition: opacity 0.3s ease;
            margin-left: 10px;
            display: flex;
            gap: 8px;
        }

        .task-btn {
            background: none;
            border: none;
            cursor: pointer;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 0.8rem;
            transition: all 0.2s ease;
        }

        .edit-btn {
            color: #667eea;
            background: rgba(102, 126, 234, 0.1);
        }

        .edit-btn:hover {
            background: rgba(102, 126, 234, 0.2);
        }

        .delete-btn {
            color: #e53e3e;
            background: rgba(229, 62, 62, 0.1);
        }

        .delete-btn:hover {
            background: rgba(229, 62, 62, 0.2);
        }

        .add-task-section {
            margin-top: 20px;
            padding: 20px;
            background: #f8fafc;
            border-radius: 16px;
            border: 2px dashed #cbd5e0;
        }

        .add-task-input {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e2e8f0;
            border-radius: 12px;
            font-size: 0.95rem;
            margin-bottom: 12px;
            transition: all 0.3s ease;
        }

        .add-task-input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .add-btn {
            background: #48bb78;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 10px;
            font-size: 0.9rem;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .add-btn:hover {
            background: #38a169;
            transform: translateY(-1px);
        }

        .edit-input {
            width: 100%;
            padding: 8px 12px;
            border: 2px solid #667eea;
            border-radius: 8px;
            font-size: 0.95rem;
            background: white;
        }

        .edit-actions {
            margin-top: 8px;
            display: flex;
            gap: 8px;
        }

        .save-btn {
            background: #48bb78;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 0.8rem;
            cursor: pointer;
        }

        .cancel-btn {
            background: #718096;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 0.8rem;
            cursor: pointer;
        }

        .progress-bar {
            width: 100%;
            height: 8px;
            background: #e2e8f0;
            border-radius: 4px;
            margin: 20px 0;
            overflow: hidden;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            border-radius: 4px;
            transition: width 0.3s ease;
            width: 0%;
        }

        .progress-text {
            text-align: center;
            font-size: 0.9rem;
            color: #718096;
            margin-top: 5px;
        }

        .error {
            color: #e53e3e;
            text-align: center;
            margin: 20px 0;
            padding: 16px;
            background: #fed7d7;
            border-radius: 12px;
            border-left: 4px solid #e53e3e;
        }

        @media (max-width: 768px) {
            .container {
                padding: 30px 20px;
                margin: 10px;
            }
            
            h1 {
                font-size: 2rem;
            }
            
            .btn {
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Task Breakdown</h1>
        <p class="subtitle">Transform your big ideas into actionable steps</p>
        
        <div class="input-section">
            <label for="taskInput">Describe your task:</label>
            <textarea 
                id="taskInput" 
                placeholder="e.g., Plan a birthday party for my 8-year-old daughter, Learn to play guitar, Start a small online business..."
            ></textarea>
        </div>

        <div class="button-container">
            <button class="btn" onclick="breakdownTask()">
                Break It Down
            </button>
        </div>

        <div class="loading" id="loading">
            <div class="spinner"></div>
            Breaking down your task...
        </div>

        <div class="result" id="result">
            <div class="task-title" id="taskTitle"></div>
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
            <div class="progress-text" id="progressText">0% Complete</div>
            <ul class="checklist" id="checklist"></ul>
            
            <div class="add-task-section">
                <input 
                    type="text" 
                    class="add-task-input" 
                    id="newTaskInput" 
                    placeholder="Add a new task..."
                    onkeypress="handleAddTaskEnter(event)"
                >
                <button class="add-btn" onclick="addNewTask()">Add Task</button>
            </div>
        </div>

        <div class="error" id="error" style="display:none;"></div>
    </div>

    <script>
        async function breakdownTask() {
            const taskInput = document.getElementById('taskInput');
            const loading = document.getElementById('loading');
            const result = document.getElementById('result');
            const error = document.getElementById('error');
            const btn = document.querySelector('.btn');
            
            const task = taskInput.value.trim();
            
            if (!task) {
                showError('Please enter a task description.');
                return;
            }
            
            // Show loading state
            loading.classList.add('show');
            result.classList.remove('show');
            error.style.display = 'none';
            btn.disabled = true;
            
            try {
                const response = await fetch('/breakdown', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ task: task })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const data = await response.json();
                
                if (data.error) {
                    throw new Error(data.error);
                }
                
                displayResult(data.title, data.subtasks);
                
            } catch (err) {
                showError('Failed to break down task: ' + err.message);
            } finally {
                loading.classList.remove('show');
                btn.disabled = false;
            }
        }
        
        function displayResult(title, subtasks) {
            const taskTitle = document.getElementById('taskTitle');
            const checklist = document.getElementById('checklist');
            const result = document.getElementById('result');
            
            taskTitle.textContent = title;
            checklist.innerHTML = '';
            
            subtasks.forEach((subtask, index) => {
                addTaskToList(subtask, index, false);
            });
            
            result.classList.add('show');
            updateProgress();
        }
        
        function addTaskToList(taskText, index, isNew = false) {
            const checklist = document.getElementById('checklist');
            const li = document.createElement('li');
            li.className = 'checklist-item';
            li.dataset.index = index;
            li.draggable = true;
            
            li.innerHTML = `
                <div class="drag-handle">⋮⋮</div>
                <input type="checkbox" id="task-${index}" onchange="updateProgress()">
                <label for="task-${index}" ondblclick="editTask(${index})">${taskText}</label>
                <div class="task-actions">
                    <button class="task-btn edit-btn" onclick="editTask(${index})" title="Edit task">✏️</button>
                    <button class="task-btn delete-btn" onclick="deleteTask(${index})" title="Delete task">🗑️</button>
                </div>
            `;
            
            // Add drag and drop event listeners
            li.addEventListener('dragstart', handleDragStart);
            li.addEventListener('dragover', handleDragOver);
            li.addEventListener('drop', handleDrop);
            li.addEventListener('dragend', handleDragEnd);
            li.addEventListener('dragenter', handleDragEnter);
            li.addEventListener('dragleave', handleDragLeave);
            
            if (isNew) {
                checklist.appendChild(li);
            } else {
                checklist.appendChild(li);
            }
        }
        
        let draggedElement = null;
        
        function handleDragStart(e) {
            draggedElement = this;
            this.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/html', this.outerHTML);
        }
        
        function handleDragOver(e) {
            if (e.preventDefault) {
                e.preventDefault();
            }
            e.dataTransfer.dropEffect = 'move';
            return false;
        }
        
        function handleDragEnter(e) {
            if (this !== draggedElement) {
                this.classList.add('drag-over');
            }
        }
        
        function handleDragLeave(e) {
            this.classList.remove('drag-over');
        }
        
        function handleDrop(e) {
            if (e.stopPropagation) {
                e.stopPropagation();
            }
            
            if (draggedElement !== this) {
                const checklist = document.getElementById('checklist');
                const draggedIndex = Array.from(checklist.children).indexOf(draggedElement);
                const targetIndex = Array.from(checklist.children).indexOf(this);
                
                if (draggedIndex < targetIndex) {
                    this.parentNode.insertBefore(draggedElement, this.nextSibling);
                } else {
                    this.parentNode.insertBefore(draggedElement, this);
                }
                
                updateTaskIndices();
            }
            
            this.classList.remove('drag-over');
            return false;
        }
        
        function handleDragEnd(e) {
            this.classList.remove('dragging');
            
            // Clean up all drag-over classes
            const items = document.querySelectorAll('.checklist-item');
            items.forEach(item => {
                item.classList.remove('drag-over');
            });
            
            draggedElement = null;
        }
        
        function editTask(index) {
            const taskItem = document.querySelector(`[data-index="${index}"]`);
            const label = taskItem.querySelector('label');
            const currentText = label.textContent;
            
            const editInput = document.createElement('input');
            editInput.type = 'text';
            editInput.className = 'edit-input';
            editInput.value = currentText;
            
            const editActions = document.createElement('div');
            editActions.className = 'edit-actions';
            editActions.innerHTML = `
                <button class="save-btn" onclick="saveTask(${index}, this)">Save</button>
                <button class="cancel-btn" onclick="cancelEdit(${index}, '${currentText.replace(/'/g, "\\'")}', this)">Cancel</button>
            `;
            
            label.style.display = 'none';
            taskItem.querySelector('.task-actions').style.display = 'none';
            
            label.parentNode.insertBefore(editInput, label.nextSibling);
            label.parentNode.insertBefore(editActions, editInput.nextSibling);
            
            editInput.focus();
            editInput.select();
            
            editInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    saveTask(index, editActions.querySelector('.save-btn'));
                } else if (e.key === 'Escape') {
                    cancelEdit(index, currentText, editActions.querySelector('.cancel-btn'));
                }
            });
        }
        
        function saveTask(index, saveBtn) {
            const taskItem = document.querySelector(`[data-index="${index}"]`);
            const editInput = taskItem.querySelector('.edit-input');
            const label = taskItem.querySelector('label');
            const newText = editInput.value.trim();
            
            if (newText) {
                label.textContent = newText;
            }
            
            cleanupEdit(taskItem);
        }
        
        function cancelEdit(index, originalText, cancelBtn) {
            const taskItem = document.querySelector(`[data-index="${index}"]`);
            cleanupEdit(taskItem);
        }
        
        function cleanupEdit(taskItem) {
            const editInput = taskItem.querySelector('.edit-input');
            const editActions = taskItem.querySelector('.edit-actions');
            const label = taskItem.querySelector('label');
            const taskActions = taskItem.querySelector('.task-actions');
            
            if (editInput) editInput.remove();
            if (editActions) editActions.remove();
            
            label.style.display = '';
            taskActions.style.display = '';
        }
        
        function deleteTask(index) {
            if (confirm('Are you sure you want to delete this task?')) {
                const taskItem = document.querySelector(`[data-index="${index}"]`);
                taskItem.remove();
                updateTaskIndices();
                updateProgress();
            }
        }
        
        function addNewTask() {
            const newTaskInput = document.getElementById('newTaskInput');
            const taskText = newTaskInput.value.trim();
            
            if (!taskText) {
                showError('Please enter a task description.');
                return;
            }
            
            const checklist = document.getElementById('checklist');
            const newIndex = checklist.children.length;
            
            addTaskToList(taskText, newIndex, true);
            newTaskInput.value = '';
            updateProgress();
        }
        
        function handleAddTaskEnter(event) {
            if (event.key === 'Enter') {
                addNewTask();
            }
        }
        
        function updateTaskIndices() {
            const taskItems = document.querySelectorAll('.checklist-item');
            taskItems.forEach((item, index) => {
                item.dataset.index = index;
                const checkbox = item.querySelector('input[type="checkbox"]');
                const label = item.querySelector('label');
                
                checkbox.id = `task-${index}`;
                label.setAttribute('for', `task-${index}`);
                label.setAttribute('ondblclick', `editTask(${index})`);
                
                const editBtn = item.querySelector('.edit-btn');
                const deleteBtn = item.querySelector('.delete-btn');
                
                editBtn.setAttribute('onclick', `editTask(${index})`);
                deleteBtn.setAttribute('onclick', `deleteTask(${index})`);
            });
        }
        
        function updateProgress() {
            const checkboxes = document.querySelectorAll('#checklist input[type="checkbox"]');
            const completed = document.querySelectorAll('#checklist input[type="checkbox"]:checked');
            const progressFill = document.getElementById('progressFill');
            const progressText = document.getElementById('progressText');
            
            const percentage = checkboxes.length > 0 ? Math.round((completed.length / checkboxes.length) * 100) : 0;
            
            progressFill.style.width = percentage + '%';
            progressText.textContent = `${percentage}% Complete (${completed.length}/${checkboxes.length} tasks)`;
            
            // Update completed items styling
            checkboxes.forEach((checkbox, index) => {
                const item = checkbox.closest('.checklist-item');
                if (checkbox.checked) {
                    item.classList.add('completed');
                } else {
                    item.classList.remove('completed');
                }
            });
        }
        
        function showError(message) {
            const error = document.getElementById('error');
            error.textContent = message;
            error.style.display = 'block';
        }
        
        // Allow Enter key to submit (with Shift+Enter for new line)
        document.getElementById('taskInput').addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                breakdownTask();
            }
        });
    </script>
</body>
</html>
"""


class TaskBreakdownApp:
    def __init__(self):
        self.api_key = None
        self.setup_gemini()
    
    def setup_gemini(self):
        # ... (this method remains unchanged)
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            print("⚠️  Warning: GEMINI_API_KEY not found in .env file!")
            return False
        
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash') # Using a slightly newer model can also help
            return True
        except Exception as e:
            print(f"❌ Error setting up Gemini API: {e}")
            return False
    
    def breakdown_task(self, task_description):
        """Use Gemini API to break down a task into smaller subtasks"""
        if not self.api_key:
            return {
                'error': 'Gemini API key not configured. Please create a .env file with GEMINI_API_KEY=your-api-key-here'
            }
        
        # --- START: THIS IS THE UPDATED PROMPT ---
        prompt = f"""
        You are an expert project manager. Your goal is to break down a task into a series of smaller, manageable subtasks.

        The number of subtasks you create should be appropriate for the complexity of the original task. A simple task like "write a thank you email" might only need 2-3 subtasks. A very complex project like "launch a new mobile app" could require 10 or more. Prioritize creating a logical and complete plan over sticking to a specific number of steps.

        Return the response in a clean JSON format with the following structure:
        {{
            "title": "A clear, concise title for the main task",
            "subtasks": [
                "Subtask 1 - specific and actionable",
                "Subtask 2 - specific and actionable",
                ...
            ]
        }}

        Guidelines for each subtask:
        - Start with an action verb (e.g., "Research", "Design", "Implement").
        - Be specific, clear, and represent a single, completable action.
        - Be logically ordered if there is a clear sequence.

        Task to break down: "{task_description}"

        Only return the JSON object, with no other text, markdown, or explanation.
        """
        # --- END: UPDATED PROMPT ---
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean up the response text to extract JSON
            response_text = re.sub(r'```json\s*', '', response_text)
            response_text = re.sub(r'```\s*$', '', response_text)
            response_text = response_text.strip()
            
            # Parse JSON
            result = json.loads(response_text)
            
            # Validate the structure
            if 'title' not in result or 'subtasks' not in result:
                raise ValueError("Invalid response structure from API")
            
            if not isinstance(result['subtasks'], list) or len(result['subtasks']) == 0:
                raise ValueError("No subtasks returned from API")
            
            return result
            
        except json.JSONDecodeError as e:
            error_details = f'Failed to parse API response as JSON. Response was: {response_text}'
            print(error_details)
            return {'error': error_details}
        except Exception as e:
            return {'error': f'API request failed: {e}'}

# Initialize the app
task_app = TaskBreakdownApp()

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/breakdown', methods=['POST'])
def breakdown():
    try:
        data = request.get_json()
        task = data.get('task', '').strip()
        
        if not task:
            return jsonify({'error': 'Task description is required'}), 400
        
        result = task_app.breakdown_task(task)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def main():
    """
    Main function to run the Flask application.
    This is called when the script is executed directly.
    """
    # Check if API key is set, which is crucial for the app to function
    if not os.getenv('GEMINI_API_KEY') or os.getenv('GEMINI_API_KEY') == 'your-api-key-here':
        print("=" * 40)
        print("❌ CRITICAL ERROR: GEMINI_API_KEY is not set!")
        print("   Please create a .env file and add your key:")
        print("   GEMINI_API_KEY=your-actual-api-key")
        print("=" * 40)
        # We don't exit here, to allow the Electron error handler to catch it
        # but the API calls will fail.

    # This is the entry point for our desktop app's backend.
    # Electron will handle the window, we just need to run the server.
    print("🚀 Starting Task Breakdown Flask server...")
    print("   Listening on http://localhost:5000")
    print("   This server is managed by the Electron application.")
    print("   Close the app window to stop the server.")
    print("=" * 40)
    
    # Run the Flask app. `debug=False` is important for production/packaged apps.
    app.run(host='localhost', port=5000, debug=False)

if __name__ == '__main__':
    main()