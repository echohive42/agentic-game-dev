import asyncio
from anthropic import AsyncAnthropic
import os
import xml.etree.ElementTree as ET
import re
from termcolor import colored
import subprocess
import traceback
import sys
import time

# Initialize Anthropic client
client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

PRINT_RESPONSE = True

# WARNING: THIS SCRIPT WILL AUTOMATICALLY EXECUTE CODE ON YOUR MACHINE. 
# THIS CAN BE POTENTIALLY DANGEROUS.
# IF YOU UNDERSTAND AND ACCEPT THIS RISK, PLEASE TYPE 'YES' TO CONTINUE.

print(colored("Welcome to Agent Game Dev!", "cyan"))
print(colored("This tool will help you create a Pygame project using AI assistance.", "cyan"))
print(colored("Please follow the prompts carefully and enjoy the game development process!", "cyan"))
print()

user_consent = input(colored("WARNING: THIS SCRIPT WILL AUTOMATICALLY EXECUTE CODE ON YOUR MACHINE. THIS CAN BE POTENTIALLY DANGEROUS. IF YOU UNDERSTAND AND ACCEPT THIS RISK, PLEASE TYPE 'YES' TO CONTINUE: ", "red")).strip().upper()

if user_consent != "YES":
    print(colored("Script Agent Game Dev.", "yellow"))
    sys.exit(0)

print(colored("User consent received. Proceeding with Agent Game Dev.", "green"))


# Remove the 'app' directory and its contents if it exists
try:
    if os.path.exists("app"):
        import shutil
        shutil.rmtree("app")
except Exception as e:
    print(colored(f"please close any terminal which has app folder open and run the game again. error: {e}", "red"))

# Function to check for consecutive user messages and add a separator
def add_separator_between_consecutive_user_messages(messages):
    for i in range(len(messages) - 1):
        if messages[i]["role"] == "user" and messages[i+1]["role"] == "user":
            messages.insert(i+1, {"role": "assistant", "content": "..."})
    return messages



# Function for planner agents to discuss and plan the project
async def plan_project(user_input, iterations):
    system_message_1 = f"""
    You are a logical, critical game design expert. Your role is to discuss and plan with a critical and rigorous eye, a Pygame project based on user input. One of the main goals is to review the logic of the code to ensure a playable and enjoyable game play experience for the user.
    Focus on game mechanics, structure, and overall design and function and method inputs inputs(proper inputs and number of inputs) and returns of functions and methods. Do not suggest external media files or images.make sure no code files need any external files. all assets must be generated within pygame. Critical objective is to keep the project structure simple while making sure no circular imports or broken imports occur. No need to discuss timelines or git commands. Main purpose is to review and evaluate the project structure so that when the final files and their descriptions are prepared the code will function without any errors.
    Remember that the game should start with a main module in the main.py file.
    here is the user input: {user_input}
    """
    
    system_message_2 = f"""
    You are a logical, critical Python architecture expert. Your role is to discuss and plan with a critical and rigorous eye the file structure for a Pygame project. One of the main goals is to review the logic of the code to ensure a playable and enjoyable game play experience for the user.
    Focus on code organization, modularity, and best practices and function and method inputs(proper inputs and number of inputs) and returns of functions and methods . Do not suggest external media files or images. make sure no code files need any external files. all assets must be generated within pygame. Critical objective is to keep the project structure simple while making sure no circular imports or broken imports occur. No need to discuss timelines or git commands.  Main purpose is to review and evaluate the project structure so that when the final files and their descriptions are prepared the code will function without any errors.
    Remember that the game should start with a main module in the main.py file.
    here is the user input: {user_input}
    """
    messages_1 = [{"role": "user", "content": f"please plan a Pygame project based on the following user input: {user_input}. Remember that the game should start with a main module in the main.py file."}]
    messages_2 = []
    
    for i in range(iterations):
        print(colored(f"Iteration {i+1} of {iterations} planning iterations", "yellow"))
        is_final = i == iterations - 1
        
        if is_final:
            
            messages_1.append({"role": "user", "content": "this is the final iteration. please provide your final game structure along with file structure you think is best for the game. don't return any directories but just the file names and descriptions. make sure to mention what imports are necessary for each file. Critical objective is to keep the project structure simple while making sure no circular imports or broken imports occur. ensure function and method inputs are accurate as well as their returns. Remember that the game should start with a main module in the main.py file(main shouldn't take any arguments)."})
        
        messages_1 = add_separator_between_consecutive_user_messages(messages_1)
        
        response_1 = await client.messages.create(
            model="claude-3-5-sonnet-20240620",
            system=system_message_1,
            messages=messages_1,
            max_tokens=4000
        )

        if PRINT_RESPONSE:
            print(colored(response_1.content[0].text, "green"))
        messages_1.append({"role": "assistant", "content": response_1.content[0].text})
        messages_2.append({"role": "user", "content": response_1.content[0].text})
        
        if is_final:
            messages_2.append({"role": "user", "content": "This is the final iteration. Please review the game design carefully and provide your final response in the following XML format:\n<game_plan>\n  <overview>Overall game description</overview>\n  <mechanics>Key game mechanics</mechanics>\n  <files>\n    <file>\n      <name>filename.py</name>\n      <description>File purpose and contents</description>\n    </file>\n    <!-- Repeat <file> element for each file -->\n  </files>\n</game_plan>. please don't return any additional directories but just the file names and descriptions along with simple description of functions and methods along with their inputs and returns. Please return descriptions for all files. we will save all files in the same folder. make sure to mention what imports are necessary for each file. Critical objective is to keep the project structure simple while making sure no circular imports or broken imports occur as well as the clear and accurate definition of function and method inputs. Remember that the game should start with a main module in the main.py file(main shouldn't take any arguments)."})
        
        messages_2 = add_separator_between_consecutive_user_messages(messages_2)
        
        response_2 = await client.messages.create(
            model="claude-3-5-sonnet-20240620",
            system=system_message_2,
            messages=messages_2,
            max_tokens=4000
        )
        
        if PRINT_RESPONSE:
            print(colored(response_2.content[0].text, "blue"))
        messages_2.append({"role": "assistant", "content": response_2.content[0].text})
        messages_1.append({"role": "user", "content": response_2.content[0].text})
    
    # Extract the XML content from the response
    xml_content = re.search(r'<game_plan>.*?</game_plan>', response_2.content[0].text, re.DOTALL)
    if xml_content:
        return xml_content.group(0)
    else:
        raise ValueError("No valid XML content found in the response")
    
# Function to call Claude 3.5 and write files
async def agent_write_file(file_name, file_description, game_plan):
    print(colored(f"Creating file '{file_name}'...", "yellow"))
    # create game folder if it doesnt exist
    os.makedirs("app", exist_ok=True)
    system_message = """
    You are a Python game development expert. Your task is to write a error free Python file for a Pygame game based on the overall project structure. Always return the full contents of the file. One of the main goals is to review the logic of the code to ensure a playable and enjoyable game play experience for the user.
    Do not include any external media files or images in your code.
    Write clean, well-commented code that follows best practices.
    The game should start with a main module in the main.py file(main shouldn't take any arguments).
    return the code for the file in the following format:
    <code>
    file_code
    </code>
    """
    
    prompt = f"""Create a Python file named '{file_name}' with the following description: {file_description}
    
    Here's the overall game plan which you should follow while writing the file:
    {game_plan}
    
    Remember, the game should start with a main module in the main.py file(main shouldn't take any arguments). Always return the full contents of the file
    """
    
    response = await client.messages.create(
        model="claude-3-5-sonnet-20240620",
        system=system_message,
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )
    
    code = response.content[0].text
    code = code.split("<code>")[1].split("</code>")[0]
    
    with open(f"app/{file_name}", "w", encoding="utf-8") as f:
        f.write(code)
    
    print(f"File '{file_name}' has been created.")

# Function to parse file structure from planner agents' discussion
def parse_file_structure(xml_string):
    root = ET.fromstring(xml_string)
    files = []
    for file_elem in root.findall('.//file'):
        name = file_elem.find('name').text
        description = file_elem.find('description').text
        files.append((name, description))
    return files

# Function to fix errors in the game files
# Function to run the game and capture error

async def run_game():
    print(colored("Running the game...", "yellow"))
    full_output = ""
    full_error = ""
    try:
        process = subprocess.Popen(
            [sys.executable, "-c", "import sys; sys.path.insert(0, 'app'); import main; main.main()"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print(colored("Game is running. Please play the game. Close the window to stop.", "cyan"))
        
        while True:
            try:
                output = process.stdout.readline()
                error = process.stderr.readline()
                
                if output:
                    full_output += output
                    print(output.strip())
                if error:
                    full_error += error
                    print(colored(f"Runtime error: {error.strip()}", "red"))
                
                if process.poll() is not None:
                    break
                
                await asyncio.sleep(0.1)
            except KeyboardInterrupt:
                print(colored("\nGame stopped by user.", "yellow"))
                process.terminate()
                break
        
        stdout, stderr = process.communicate()
        full_output += stdout
        full_error += stderr
        
        if process.returncode != 0:
            full_error += f"\nProcess exited with return code {process.returncode}"
        
    except Exception as e:
        full_error += f"\nError running game: {str(e)}\n{traceback.format_exc()}"
    
    error_summary = ""
    if full_error:
        error_summary += f"Runtime errors:\n{full_error}\n"
    if "error" in full_output.lower() or "exception" in full_output.lower():
        error_summary += f"Possible errors in output:\n{full_output}\n"
    
    if error_summary:
        print(colored(error_summary, "red"))
        return error_summary
    else:
        print(colored("Game completed successfully", "green"))
        return None

async def create_game():
    
    max_attempts = 10
    while True:
        error_summary = await run_game()
        if error_summary is None:
            print(colored("Game ran successfully!", "green"))
            feedback = input(colored("Please provide your feedback on the game for iterative improvement (or type 'quit' to exit): ", "green"))
            if feedback.lower() == 'quit':
                break
            print("Updating game based on feedback...")
            await update_game_files(feedback)
            count_lines_of_code()
        else:
            print(colored(f"Errors detected:\n{error_summary}", "red"))
            for attempt in range(max_attempts):
                print(f"Attempt {attempt + 1} to fix the errors...")
                await fix_game_files(error_summary)
                count_lines_of_code()
                time.sleep(1)  # Allow time for files to be written
                
                # Try running the game again after fixing
                error_summary = await run_game()
                if error_summary is None:
                    print(colored("Errors fixed successfully!", "green"))
                    break
            else:
                print(colored(f"Failed to fix all errors after {max_attempts} attempts.", "red"))
                user_choice = input(colored("Press Enter to continue error correcting, or type 'quit' to exit: ", "yellow")).lower()
                if user_choice == 'quit':
                    break



# Function to fix errors in the game files
async def fix_game_files(error_message):
    print(colored("Attempting to fix the error...", "yellow"))
    
    # Extract all filenames from the error message
    error_filenames = re.findall(r'.*?([^/\\]+\.py)"', error_message)
    error_filenames = list(set(error_filenames))  # Remove duplicates
    
    # Remove agent_game_maker.py from the list if present
    error_filenames = [f for f in error_filenames if f != 'agent_game_maker.py']
    
    file_contents = {}

    for filename in os.listdir('app'):
        if filename.endswith('.py'):
            with open(os.path.join('app', filename), 'r') as f:
                file_contents[filename] = f.read()
    
    if error_filenames:
        print(f"Error occurred in files: {', '.join(error_filenames)}")
    else:
        print("Could not determine specific files causing the error")
    
    print(f"Sending all files for error correction: {', '.join(file_contents.keys())}")

    system_message = """
    You are a Python game development expert. Your task is to fix errors in Pygame project files.
    Analyze the error message and the contents of the game files, then provide the corrected versions of the files.
    Remember that the game should start with a main module in the main.py file(main shouldn't take any arguments).
    carefully reason about the error in a step by step manner ahead of providing the corrected code. no external files are allowed within the game. One of the main goals is to review the logic of the code to ensure a playable and enjoyable game play experience for the user.
    <reasoning>
    reasoning about the error
    </reasoning>
    Return the corrected file contents in the following format only for the files that requires correction:
    <file name="filename.py">
    corrected_file_contents
    </file>
    """
    
    prompt = f"""An error occurred while running the Pygame project. Here's the error message:
    
    {error_message}
    
    Here are the contents of the files involved in the error:
    
    {file_contents}
    
    Please analyze the error and provide corrected versions of the files to resolve the error. return the full content of the files Remember that the game should start with a main module in the main.py file(main shouldn't take any arguments)."""
    
    response = await client.messages.create(
        model="claude-3-5-sonnet-20240620",
        system=system_message,
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )

    if PRINT_RESPONSE:
        print(colored(response.content[0].text, "magenta"))
    # Extract corrected file contents from the response
    corrected_files = re.findall(r'<file name="(.*?)">(.*?)</file>', response.content[0].text, re.DOTALL)
    
    if corrected_files:
        for filename, content in corrected_files:
            file_path = os.path.join('app', filename)
            with open(file_path, 'w', encoding="utf-8") as f:
                f.write(content.strip())
            print(f"Updated file: {filename}")
            
            # Ensure the file is written by reading it back
            with open(file_path, 'r') as f:
                written_content = f.read()
            if written_content.strip() != content.strip():
                print(f"Warning: File {filename} may not have been written correctly.")
    
        # Clear Python's module cache for the app directory, this may not be necessary
        for module_name in list(sys.modules.keys()):
            if module_name.startswith('app.'):
                del sys.modules[module_name]
        
        time.sleep(1)  # Add a small delay to ensure files are fully written
    else:
        print("No corrected file content found in the response.")

async def update_game_files(user_feedback):
    # Gather all existing game files
    game_files = {}
    for root, dirs, files in os.walk('app'):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    game_files[file] = f.read()

    # Prepare the prompt for the API
    file_contents = "\n\n".join([f"File: {filename}\n\n{content}" for filename, content in game_files.items()])
    
    prompt = f"""Here are the current contents of the Pygame project files:

    {file_contents}

    The user has provided the following feedback about the game:

    {user_feedback}

    Please analyze the feedback and suggest updates to the game files to address the user's comments. 
    Provide the full updated content for any files that need changes. 
    Return the updated file contents in the following format only for the files that require updates:
    <file name="filename.py">
    updated_file_contents
    </file>
    always return the full content of the files
    game should start with a main module in the main.py file(main shouldn't take any arguments).
    """

    system_message = """You are an expert Python and Pygame developer. Your task is to update a Pygame project based on user feedback. 
    Analyze the current game files and the user's feedback, then provide updated versions of any files that need changes to address the feedback. Always return the full content of the files. One of the main goals is to review the logic of the code to ensure a playable and enjoyable game play experience for the user. no external files are allowed within the game
    Ensure that your changes are consistent with the existing code structure and Pygame best practices. Remember that the game should start with a main module in the main.py file(main shouldn't take any arguments)."""

    response = await client.messages.create(
        model="claude-3-5-sonnet-20240620",
        system=system_message,
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )
    
    if PRINT_RESPONSE:
        print(colored(response.content[0].text, "magenta"))

    # Extract updated file contents from the response
    updated_files = re.findall(r'<file name="(.*?)">(.*?)</file>', response.content[0].text, re.DOTALL)

    if updated_files:
        for filename, content in updated_files:
            file_path = os.path.join('app', filename)
            with open(file_path, 'w', encoding="utf-8") as f:
                f.write(content.strip())
            print(f"Updated file: {filename}")

            # Ensure the file is written correctly by reading it back
            with open(file_path, 'r') as f:
                written_content = f.read()
            if written_content.strip() != content.strip():
                print(f"Warning: File {filename} may not have been written correctly.")

        # Clear Python's module cache for the app directory, this may not be necessary
        for module_name in list(sys.modules.keys()):
            if module_name.startswith('app.'):
                del sys.modules[module_name]

        time.sleep(1)  # Add a small delay to ensure files are fully written
    else:
        print("No updates were necessary based on the user's feedback.")

def count_lines_of_code():
    total_lines = 0
    for filename in os.listdir('app'):
        if filename.endswith('.py'):
            with open(os.path.join('app', filename), 'r') as file:
                total_lines += sum(1 for line in file if line.strip())
    print(colored(f"Total lines of code in writen by agent_game_maker: {total_lines}", "yellow"))


# Main function to orchestrate the game creation process
async def create_game():
    user_input = input(colored("Describe the Pygame game you want to create: ", "green"))
    iterations = int(input(colored("How many planning iterations do you want? ", "green")))
    
    print("Planning the game structure...")
    final_plan = await plan_project(user_input, iterations)
    print(colored("writing game plan to game_plan.xml", "yellow"))
    with open("game_plan.xml", "w", encoding="utf-8") as f:
        f.write(final_plan)
    
    file_structure = parse_file_structure(final_plan)

    
    print("Creating game files...")
    os.makedirs("app", exist_ok=True)
    
    tasks = []
    for file_name, file_description in file_structure:
        task = asyncio.create_task(agent_write_file(file_name, file_description, final_plan))
        tasks.append(task)
    
    await asyncio.gather(*tasks)

    count_lines_of_code()
    
    print("Game creation complete!")
    print("Final game plan:")
    # print(final_plan)
    
    # Run the game in a loop to catch and fix errors, then enter feedback loop
    max_attempts = 10
    while True:
        error_message = await run_game()
        if error_message is None:
            print(colored("Game ran successfully!", "green"))
            feedback = input(colored("Please provide your feedback on the game for iterative improvement: ", "green"))
            print("Updating game based on feedback...")
            await update_game_files(feedback)
            count_lines_of_code()
        else:
            print(colored(f"Error detected: {error_message}", "red"))
            for attempt in range(max_attempts):
                print(f"Attempt {attempt + 1} to fix the errors...")
                await fix_game_files(error_message)
                count_lines_of_code()
                time.sleep(1)  # Allow time for files to be written
                
                # Try running the game again after fixing
                error_message = await run_game()
                if error_message is None:
                    print(colored("Errors fixed successfully!", "green"))
                    break
            else:
                print(colored(f"Failed to fix all errors after {max_attempts} attempts.", "red"))
                user_choice = input(colored("Press Enter to continue error correcting, or type 'no' to quit: ", "yellow")).lower()
                if user_choice == 'no':
                    return

# Run the game creation process
if __name__ == "__main__":
    asyncio.run(create_game())

