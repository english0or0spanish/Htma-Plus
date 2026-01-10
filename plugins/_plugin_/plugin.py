import requests
import os
import subprocess
import urllib3
import zipfile
import glob

subprocess.run(["python", "CLI_PACK\\register.py"])

subprocess.run(["pip", "install", "gdown"])

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

while True:    
    print("Type 1 to begin Downloading a plugin and type 2 to begin Uploading a plugin")
    ud = input()
    print("you have chosen " + ud + ", to proceed type " + ud + " again, to change your choice please type the other option")
    ud = input()
    if ud == "1":
        print("Please type the name of the plugin you want to download then type the number next to the plugin you want to download")
        name = input()

        GREEN = '\033[92m'
        RESET = '\033[0m'

        try:
            resp = requests.get(f"http://api.piscript.org/requests/q7m2v9t4c1x8r5p0lbdwz6yhnfuj3sk8q1m5v9t0r2c7x4p6lbdwz8yhfnu3sj5k1mq7v2t9c4x1r8p5l0bdwz6yhnfu/?query={name}", timeout=5)
            resp.raise_for_status()
            results = resp.json()
        except Exception as e:
            print("Error fetching search results:", e)
            results = []

        if not results:
            print("No plugins found for:", name)
        else:
            print("\nSearch results:")
            for i, plugin in enumerate(results, 1):
                display_name = plugin["name"]
                if plugin["type"] == "official":
                    display_name = f"\033[92m{display_name}\033[0m"
                print(f"{i}. {display_name} [ID: {plugin['id']}]")



        choice = input("\nType the list number OR plugin ID to download (or anything else to cancel): ")

        selected_id = None
        selected_name = None
        selected_type = None
        
        if choice.isdigit():
            choice_num = int(choice)
            
            if results:
                for plugin in results:
                    if plugin['id'] == choice_num:
                        selected_id = plugin['id']
                        selected_name = plugin['name']
                        selected_type = plugin['type']
                        break
            
            if not selected_id:
                selected_id = choice_num
        
        if selected_id:
            try:
                print(f"Fetching download link for plugin ID {selected_id}...")
                fetch_resp = requests.get(f"https://hapi.piscript.org/requests/f9x2m7q4t1c8r5p0lbdwz6yhnfu3sj9k1v8t4c2x7m5p0rldwz6yhfnu3sj8k1m9q4t2v7c5x0p/?id={selected_id}", timeout=5, verify=False)
                fetch_resp.raise_for_status()
                plugin_data = fetch_resp.json()
                
                selected_name = plugin_data['name']
                selected_type = plugin_data['type']
                download_link = plugin_data['download_link']
                
                script_dir = os.path.dirname(os.path.abspath(__file__))
                download_dir = os.path.join(script_dir, "plugins")
                extract_dir = os.path.join(script_dir, "..")
                os.makedirs(download_dir, exist_ok=True)
        
                print(f"Downloading {selected_name} (ID: {selected_id})...")
        
                subprocess.run([
                    "gdown",
                    download_link,
                    "--folder",
                    "-O",
                    download_dir,
                    "--fuzzy"
                ])
                
                for zip_path in glob.glob(os.path.join(download_dir, "*.zip")):
                    with zipfile.ZipFile(zip_path, 'r') as archive:
                        archive.extractall(extract_dir)
                        print(f"Extracted: {zip_path}")
                    os.remove(zip_path)
                    print(f"Deleted: {zip_path}")
        
                print("Download complete.")
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    print(f"Plugin with ID {selected_id} not found.")
                else:
                    print(f"Error fetching plugin: {e}")
            except Exception as e:
                print(f"Error downloading plugin: {e}")
        else:
            print("Cancelled.")




        
    else:
        if ud == "2":
            print("Please type the full path of the plugin you want to upload")
            fullpath = input()
            print("'" + fullpath + "'")
            print("Is that correct? If yes type 1. If else type anything other than '1'")
            uconfirmation = input()
            if uconfirmation == "1":
                print("temp")
                # upload logic
            else:
                print("Please type the full path of the plugin you want to upload")
                fullpath = input()
                # upload logic
        else:
           continue
