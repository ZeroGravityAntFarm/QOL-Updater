import customtkinter
import os
import GPUtil
import json
import subprocess
import time
#import pyi_splash
import webbrowser
import hashlib
import shutil
import requests
import zipfile

from tkinter import filedialog
from pathlib import Path
from PIL import ImageTk
from packaging import version

customtkinter.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue"


vulkan_data = ""


#Get gpu hardware details and validate vulkan support
def check_gpu_support():
    systemInfo = {}

    with open("assets/supported-cards.json") as vulkanData:
        vulkanData = json.load(vulkanData)
        
    gpus = GPUtil.getGPUs()
    for gpu in gpus:
        for card in vulkanData["data"]:
            if gpu.name == card["gpuname"]:
                systemInfo["gpuName"] = gpu.name
                systemInfo["vulkanSupported"] = True
                systemInfo["vulkanSupportedVersion"] = card["api"]
                systemInfo["vulkaSupportedDriverVersion"] = card["driver"]
                systemInfo["make"] = card["vendor"]

        if not systemInfo["vulkanSupported"]:
            systemInfo["gpuName"] = gpu.name
            systemInfo["vulkanSupported"] = False

    return systemInfo


#sha1 hash
def sha1_check(file_path):
    try:
        hash = hashlib.sha1(open(file_path,'rb').read()).hexdigest()
        return hash
    
    except:
        return f"{file_path} Not Found"


#Get vulkan version on local machine
def get_vulkan_version():
    global vulkan_data
    
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    
    vulkanInfo = subprocess.Popen(["assets\\vulkaninfo.exe"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
    stdout, stderr = vulkanInfo.communicate()


    for line in stdout.splitlines():
        if "Vulkan Instance Version:" in str(line):
            line = line.decode('UTF-8')
            line = line.split(": ")[1]

            vulkan_data = line
            break
    
    vulkanInfo.kill()
    vulkanInfo.wait()

    return


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        #Configure Window
        self.title("QOL Updater")
        self.geometry(f"{800}x{650}")

        #Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3, 4), weight=0)
        self.grid_rowconfigure((0, 1, 2, 3), weight=1)

        # Sidebar Widgets
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="QOL 6", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.sidebar_button_1 = customtkinter.CTkButton(self.sidebar_frame, command=self.open_ed_directory)
        self.sidebar_button_1.grid(row=1, column=0, padx=20, pady=10)

        self.sidebar_button_2 = customtkinter.CTkButton(self.sidebar_frame, command=self.verify_files)
        self.sidebar_button_2.grid(row=2, column=0, padx=20, pady=10)

        self.sidebar_button_3 = customtkinter.CTkButton(self.sidebar_frame)
        self.sidebar_button_3.grid(row=3, column=0, padx=20, pady=10)

        self.sidebar_button_4 = customtkinter.CTkButton(self.sidebar_frame, command=self.open_discord)
        self.sidebar_button_4.grid(row=7, column=0, padx=20, pady=10)

        #Configure Sidbar Buttons
        self.sidebar_button_1.configure(text="Apply Updates")
        self.sidebar_button_2.configure(text="Verify Files")
        self.sidebar_button_3.configure(text="Revert Changes")
        self.sidebar_button_4.configure(text="Discord")

        #Textbox for logging
        self.textbox = customtkinter.CTkTextbox(self, width=250)
        self.textbox.grid(row=0, column=1, padx=(20, 0), pady=(20, 0), rowspan=4, sticky="nsew")

        #Tabs for advanced config
        self.tabview = customtkinter.CTkTabview(self, width=250)
        self.tabview.grid(row=0, column=2, padx=(20, 0), pady=(20, 20), sticky="nsew")

        self.tabview.add("DXVK")
        self.tabview.add("CEF")
        self.tabview.add("Stats")
        self.tabview.add("FMM")
        self.tabview.add("Scheme")


        self.tabview.tab("DXVK").grid_columnconfigure(0, weight=1)  # configure grid of individual tabs
        self.tabview.tab("CEF").grid_columnconfigure(0, weight=1)
        self.tabview.tab("Stats").grid_columnconfigure(0, weight=1)
        self.tabview.tab("FMM").grid_columnconfigure(0, weight=1)
        self.tabview.tab("Scheme").grid_columnconfigure(0, weight=1)


        # DXVK Checkbox
        self.checkbox_DXVK_1 = customtkinter.CTkCheckBox(master=self.tabview.tab("DXVK"))
        self.checkbox_DXVK_1.grid(row=0, column=0, pady=(20, 0), padx=20, sticky="n")
        self.checkbox_DXVK_1.configure(text="DXVK")
        self.checkbox_DXVK_1.select()

        self.checkbox_DXVK_2 = customtkinter.CTkCheckBox(master=self.tabview.tab("DXVK"))
        self.checkbox_DXVK_2.grid(row=1, column=0, pady=(20, 0), padx=20, sticky="n")
        self.checkbox_DXVK_2.configure(text="DXVK Cache")
        self.checkbox_DXVK_2.select()

        # CEF Checkbox
        self.checkbox_CEF_1 = customtkinter.CTkCheckBox(master=self.tabview.tab("CEF"))
        self.checkbox_CEF_1.grid(row=0, column=0, pady=(20, 0), padx=20, sticky="n")
        self.checkbox_CEF_1.configure(text="CEF Fixes")
        self.checkbox_CEF_1.select()

        # Stats Checkbox
        self.checkbox_STATS_1 = customtkinter.CTkCheckBox(master=self.tabview.tab("Stats"))
        self.checkbox_STATS_1.grid(row=0, column=0, pady=(20, 0), padx=20, sticky="n")
        self.checkbox_STATS_1.configure(text="zgaf.io Stat Reporting")
        self.checkbox_STATS_1.select()

        self.checkbox_STATS_3 = customtkinter.CTkCheckBox(master=self.tabview.tab("Stats"))
        self.checkbox_STATS_3.grid(row=1, column=0, pady=(20, 0), padx=20, sticky="n")
        self.checkbox_STATS_3.configure(text="Add Active Masters")
        self.checkbox_STATS_3.select()

        self.checkbox_STATS_2 = customtkinter.CTkCheckBox(master=self.tabview.tab("Stats"))
        self.checkbox_STATS_2.grid(row=2, column=0, pady=(20, 0), padx=20, sticky="n")
        self.checkbox_STATS_2.configure(text="Remove Dead Masters")
        self.checkbox_STATS_2.select()

        # FMM Checkbox
        self.checkbox_FMM_1 = customtkinter.CTkCheckBox(master=self.tabview.tab("FMM"))
        self.checkbox_FMM_1.grid(row=0, column=0, pady=(20, 0), padx=20, sticky="n")
        self.checkbox_FMM_1.configure(text="Update FMM")
        self.checkbox_FMM_1.select()

        # Scheme Checkbox
        self.checkbox_Scheme_1 = customtkinter.CTkCheckBox(master=self.tabview.tab("Scheme"))
        self.checkbox_Scheme_1.grid(row=0, column=0, pady=(20, 0), padx=20, sticky="n")
        self.checkbox_Scheme_1.configure(text="Add Pauwlo's Eldewrito Scheme Handler")
        self.checkbox_Scheme_1.select()


    def change_appearance_mode_event(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)

    #Get config file
    def get_config(self):
        #self.log("Loading Config...", self.textbox)
        try:
            with open("assets/config.json") as config:
                qolConfig = json.load(config)
                return qolConfig

        except Exception as e:
            self.log("Could not find config assets/config.json", self.textbox)
            self.log(e, self.textbox)


    #Pull latest release from github and restart
    def self_update(self):
        qolConfig = self.get_config()
        gitApi = qolConfig["config"]["update_endpoint"]

        try:
            response = requests.get(gitApi)
            githubReleases = response.json()
        
        except:
            self.log(f"Could not access {qolConfig['config']['update_endpoint']}", self.textbox)
            return


        if version.parse(githubReleases[0]["tag_name"]) > version.parse(qolConfig["config"]["version"]):
            self.log(f"New Version Found!", self.textbox)

            try:
                self.log(f"Downloading {githubReleases[0]['zipball_url']}", self.textbox)
                response = requests.get(githubReleases[0]["zipball_url"], stream=True)

            except:
                self.log(f"Failed to dowload from {githubReleases[0]['zipball_url']}", self.textbox)
                return

            #Write new updater to assets folder
            with open("dist/update.zip", "wb") as f:
                f.write(response.content)

                with zipfile.ZipFile("dist/update.zip", 'r') as zip_ref:
                    zip_ref.extractall(os.getcwd())


                #subprocess.Popen(["assets\\update.exe"])
                exit()
        
        else:
            self.log(f"No Updates Found", self.textbox)
            return
    

    #This should be our entry point
    def startup_Tasks(self):
        qolConfig = self.get_config()

        if qolConfig["config"]["checkForUpdates"]:
            self.log("Checking for updates...", self.textbox)
            self.self_update()


    #Grab and validate game directory
    def open_ed_directory(self):
        file_path = filedialog.askdirectory()
        ed_path = Path(file_path + "/eldorado.exe")

        if ed_path.is_file():
            self.log("", self.textbox)
            self.log("Eldorado Found!", self.textbox)

            #Get GPU and Vulkan support information
            gpu_support = check_gpu_support()

            for key, value in gpu_support.items():
                self.log(key + ": " + str(value), self.textbox)

            get_vulkan_version()

            #Give vulkaninfo enough time to run
            time.sleep(2)
            self.log("Vulkan version: " + str(vulkan_data), self.textbox)

        elif not file_path:
            pass

        else:
            self.log("Invalid Game Directory", self.textbox)

        return


    def open_discord(self):
        webbrowser.open("https://discord.gg/ag6s9BnJ", new=1)


    def verify_files(self):
        #What do we want to verify?
        #Everything in dewrito.json?
        #Updater files?
        file_path = filedialog.askdirectory()
        ed_path = Path(file_path + "/eldorado.exe")

        if ed_path.is_file():
            self.log("", self.textbox)
            self.log("Verifying Game Files...", self.textbox)
        
        else:
            self.log("", self.textbox)
            self.log("Invalid Game Directory", self.textbox)

        with open(file_path + "/mods/dewrito.json") as dewritoJson:
            dewritoJson = json.load(dewritoJson)

            for fileName, filesha1 in dewritoJson["gameFiles"].items():
                if "bink\\" in fileName:
                    continue

                file_sum = sha1_check(file_path + "/" + fileName)

                if file_sum == filesha1:
                    self.log(fileName + " CLEAN", self.textbox)
                    
                else:
                    self.log(fileName + " DIRTY", self.textbox)


    #Log to our textbox
    def log(self, message, textbox):
        t = time.localtime()
        current_time = time.strftime("%H:%M:%S", t)
        textbox.insert(customtkinter.END, f"[{current_time}] - {message}\n")
        self.textbox.see(customtkinter.END)

        
if __name__ == "__main__":
    app = App()
    app.iconpath = ImageTk.PhotoImage(file=os.path.join("assets","icon.png"))
    app.wm_iconbitmap()
    app.iconphoto(False, app.iconpath)
    #pyi_splash.close()
    app.after_idle(app.startup_Tasks)
    app.mainloop()

    