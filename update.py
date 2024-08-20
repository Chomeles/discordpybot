import os
import subprocess

# Step 1: Git pull from the given URL
def git_pull(repo_url):
    try:
        subprocess.run(['git', 'pull', repo_url], check=True)
        print(f"Successfully cloned the repository from {repo_url}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to clone the repository: {e}")
        return False
    return True

# Step 2: Ask for API key
def get_api_key():
    return input("Please enter your discord-bot-key: ")

# Step 3: Write to bot_run.py
def write_bot_run_file(api_key):
    content = f"""
import discord_related

discord_related.bot.run('{api_key}')
"""
    with open("bot_run.py", "w") as file:
        file.write(content)
    print("bot_run.py has been created successfully.")

# Main function to execute the steps
def main():
    repo_url = "https://github.com/Chomeles/discordpybot.git"
    subprocess.run(['rm', 'bot_run.py'])
    subprocess.run(['rm', 'channels.py'])
    if git_pull(repo_url):
        api_key = get_api_key()
        write_bot_run_file(api_key)

if __name__ == "__main__":
    main()
