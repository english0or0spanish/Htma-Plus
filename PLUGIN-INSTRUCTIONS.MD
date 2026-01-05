# How to make a plugin

## Step 1. Make a folder called what you want to call your plugin with a _ at the start and at the end of your plugins folder name and then place it inside of the plugins folder.
## Step 2. Inside that newly created folder create a 'plugin.json' file.
## Step 3. add 
'{
    "name": "myplugin",
    "type": "js",
    "network": true,
    "rts": true,
    "args": [
        "mypluginargument"
    ],
    "scripts": [
        "myscript.py"
    ],
    "custom": {
        "mycustomconfigvalue": 2
    }
}'
## to plugin.json
## Step 4. add your script to the plugin folder and code it (PYTHON ONLY)

### Note: rts stands for return to script which if enabled should run the scripts defined with all the TMP files it creates containing data
