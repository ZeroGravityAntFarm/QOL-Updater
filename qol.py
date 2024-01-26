import customtkinter
import os
import GPUtil
import json
import subprocess
import time
import pyi_splash
import webbrowser
import hashlib
import shutil
import requests
import zipfile

from tkinter import filedialog
from pathlib import Path
from PIL import ImageTk
from packaging import version
from win32api import GetFileVersionInfo, LOWORD, HIWORD

customtkinter.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue"


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
        print(file_path)
        print(hash)
        return hash
    
    except:
        return f"{file_path} Not Found"


#Generate shader cache
def gen_ShaderCache(fpath):
    try:
        shaderGen = subprocess.Popen([fpath + "/maps/update/UPDATE.bat"], cwd=fpath + '/maps/update/' ,stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        stdout, stderr = shaderGen.communicate()

        if stderr:
            print(stderr)
        
        shaderGen.wait()

    except Exception as e:
        return False, e

    return True, "Shader Gen Success!"


#Revert shader cache tag changes
def revert_ShaderCache(fpath):
    try:
        shaderGenReset = subprocess.Popen([fpath + "/maps/update/RESET.bat"], cwd=fpath + '/maps/update/' ,stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        stdout, stderr = shaderGenReset.communicate()

        if stderr:
            print(stderr)
        
        shaderGenReset.wait()

    except Exception as e:
        return False, e

    return True, "Disable Shader Finished!"


#Check for dewrito_prefs and set game.firstrun
def pre_tasks(fpath):
    try:
        if os.path.exists(fpath + "/dewrito_prefs.cfg"):
            with open(fpath + "/dewrito_prefs.cfg", "r") as dewprefs:
                data = dewprefs.readlines()

                for i in range(len(data)):
                    if 'Game.FirstRun "1"' in data[i]:
                        return True, "Already patched first run."
    
                    elif 'Game.FirstRun "0"' in data[i]:
                        data[i] = 'Game.FirstRun "1"\n'
                        break

            with open(fpath + "/dewrito_prefs.cfg", "w") as dewprefs:
                dewprefs.writelines(data)

            return True, "Set Game.FirstRun 1"

        else:
            try:
                shutil.copyfile("assets/dewrito_prefs.cfg", fpath + "/dewrito_prefs.cfg")
                return True, "No dewrito_prefs.cfg detected, supplying template."

            except Exception as e:
                return False, e

    except Exception as e:
        return False, e


#Get vulkan version on local machine
def get_vulkan_version():
    
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    
    vulkanInfo = subprocess.Popen(["assets\\vulkaninfo.exe"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
    stdout, stderr = vulkanInfo.communicate()

    if stderr:
        vulkan_data = stderr

    for line in stdout.splitlines():
        if "Vulkan Instance Version:" in str(line):
            line = line.decode('UTF-8')
            line = line.split(": ")[1]

            vulkan_data = line
            break
    
    vulkanInfo.kill()
    vulkanInfo.wait()

    return vulkan_data


#Update server browser in dewrito_prefs.cfg
def update_dewcfg(fpath):
    with open(fpath + "/dewrito_prefs.cfg", "r") as dewprefs:
        data = dewprefs.readlines()

        for i in range(len(data)):
            if "Game.MenuURL" in data[i]:
                data[i] = 'Game.MenuURL "http://ed6browser.thebeerkeg.net/" \n'
                
                with open(fpath + "/dewrito_prefs.cfg", "w") as dewprefs:
                    dewprefs.writelines(data)

                    return True, "Updated server browser!"
    
        return False, "Failed to update server browser."


def update_stats(fpath):
    try:
        if os.path.exists(fpath + "/mods/dewrito.json"):
            os.remove(fpath + "/mods/dewrito.json")

        shutil.copyfile("assets/dewrito.json", fpath + "/mods/dewrito.json")
        return True, "Updated dewrito.json!"
    
    except Exception as e:
        return False, e
    

def copy_binkw32(fpath):
    try:
        shutil.copyfile("assets/binkw32.dll", fpath + "/bink32.dll")
        return True, "Updated binkw32.dll"
    
    except Exception as e:
        return False, e


def copy_chat(fpath):
    try:
        shutil.copyfile("assets/mods/ui/web/screens/scoreboard/scoreboard.js", fpath + "/mods/ui/web/screens/scoreboard/scoreboard.js")
        shutil.copyfile("assets/mods/ui/web/screens/chat/chat.js", fpath + "/mods/ui/web/screens/chat/chat.js")
        shutil.copyfile("assets/mods/ui/web/screens/chat/chat.css", fpath + "/mods/ui/web/screens/chat/chat.css")
        shutil.copyfile("assets/mods/ui/web/screens/chat/index.html", fpath + "/mods/ui/web/screens/chat/index.html")
        shutil.copyfile("assets/mods/ui/web/screens/title/title.js", fpath + "/mods/ui/web/screens/title/title.js")

        return True, "Patched annoucenment, scoreboard, and chat.js"
    
    except Exception as e:
        return False, e


def copy_fmm(fpath):
    try:
        if not os.path.exists(fpath + "/FMM.exe"):
            fmm_new = GetFileVersionInfo("assets/FMM.exe", "\\")
            fmmNewMS = fmm_new["FileVersionMS"]
            fmmNewLS = fmm_new["FileVersionLS"]
            fmmNewVersion = str(HIWORD(fmmNewMS)) + "." + str(LOWORD(fmmNewMS)) + "." + str(HIWORD(fmmNewLS)) + "." + str(LOWORD(fmmNewLS))

            shutil.copyfile("assets/FMM.exe", fpath + "/FMM.exe")
            return True, "Installed FMM " + fmmNewVersion + " ✔️"
    
        else:
            fmm_new = GetFileVersionInfo("assets/FMM.exe", "\\")
            fmm_old = GetFileVersionInfo(fpath + "/FMM.exe", "\\")

            fmmNewMS = fmm_new["FileVersionMS"]
            fmmNewLS = fmm_new["FileVersionLS"]

            fmmOldMS = fmm_old["FileVersionMS"]
            fmmOldLS = fmm_old["FileVersionLS"]

            fmmNewVersion = str(HIWORD(fmmNewMS)) + "." + str(LOWORD(fmmNewMS)) + "." + str(HIWORD(fmmNewLS)) + "." + str(LOWORD(fmmNewLS))
            fmmOldVersion = str(HIWORD(fmmOldLS)) + "." + str(LOWORD(fmmOldLS)) + "." + str(HIWORD(fmmOldLS)) + "." + str(LOWORD(fmmOldLS))

            if version.parse(fmmNewVersion) > version.parse(fmmOldVersion):
                os.remove(fpath + "/FMM.exe")
                shutil.copyfile("assets/FMM.exe", fpath + "/FMM.exe")
                
                return True, "Updated FMM to " + fmmNewVersion + " ✔️"
                
            else:
                return True, "FMM " + fmmOldVersion + " already up to date ✔️"

    except Exception as e:
        return False, e


def copy_Update(fpath):
    try:
        if not os.path.isdir(fpath + "/maps/update"):
            shutil.copytree("assets/maps/update", fpath + "/maps/update")
            return True, "Copied shader updater"
        
        else:
            return True, "Shader tools found!"
    
    except Exception as e:
        return False, e


def copy_vulkans(fpath):
    try:
        shutil.copyfile("assets/DXVKs/d3d9.dll", fpath + "/d3d9.dll")
        shutil.copyfile("assets/DXVKs/dxvk.conf", fpath + "/dxvk.conf")
        shutil.copyfile("assets/DXVKs/eldorado.dxvk-cache", fpath + "/eldorado.dxvk-cache")

        return True, "Copied DXVK"
    
    except Exception as e:
        return False, e



def copy_vulkana(fpath):
    try:
        shutil.copyfile("assets/DXVKa/d3d9.dll", fpath + "/d3d9.dll")
        shutil.copyfile("assets/DXVKa/dxvk.conf", fpath + "/dxvk.conf")
        shutil.copyfile("assets/DXVKa/eldorado.dxvk-cache", fpath + "/eldorado.dxvk-cache")

        return True, "Copied DXVK"
    
    except Exception as e:
        return False, e


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        #Configure Window
        self.title("QOL Updater v0.1.4")
        self.geometry(f"{800}x{450}")

        #Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3, 4), weight=0)
        self.grid_rowconfigure((0, 1, 2, 3), weight=1)

        # Sidebar Widgets
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        #self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="QOL 6", font=customtkinter.CTkFont(size=20, weight="bold"))
        #self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.sidebar_button_1 = customtkinter.CTkButton(self.sidebar_frame, command=self.open_ed_directory)
        self.sidebar_button_1.grid(row=0, column=0, padx=20, pady=10)

        #self.sidebar_button_2 = customtkinter.CTkButton(self.sidebar_frame, command=self.reset_shaders)
        #self.sidebar_button_2.grid(row=1, column=0, padx=20, pady=10)

        self.sidebar_button_3 = customtkinter.CTkButton(self.sidebar_frame, command=self.open_guide)
        self.sidebar_button_3.grid(row=5, column=0, padx=20, pady=10)

        self.sidebar_button_4 = customtkinter.CTkButton(self.sidebar_frame, command=self.open_fileshare)
        self.sidebar_button_4.grid(row=6, column=0, padx=20, pady=10)

        self.sidebar_button_5 = customtkinter.CTkButton(self.sidebar_frame, command=self.open_discord)
        self.sidebar_button_5.grid(row=7, column=0, padx=20, pady=10)

        #Configure Sidbar Buttons
        self.sidebar_button_1.configure(text="Apply Updates")
        #self.sidebar_button_2.configure(text="Disable Shader Cache")
        self.sidebar_button_3.configure(text="ElDewrito Guide")
        self.sidebar_button_4.configure(text="Fileshare")
        self.sidebar_button_5.configure(text="Discord")

        #Tabs for advanced config
        self.tabview = customtkinter.CTkTabview(self, width=250)
        self.tabview.grid(row=0, column=1, columnspan=2, padx=(20, 20), pady=(20, 5), sticky="nsew")

        #Textbox for logging
        self.textbox = customtkinter.CTkTextbox(self, width=250)
        self.textbox.grid(row=1, column=1, columnspan=2, rowspan=4, padx=(20, 20), pady=(5, 20), sticky="nsew")

        self.tabview.add("Game Chat")
        self.tabview.add("dewrito.json")
        self.tabview.add("FMM")
        self.tabview.add("Crash Fixes")
        self.tabview.add("Experimental")
        self.tabview._segmented_button.grid(sticky="w")

        #Configure grid of individual tabs
        self.tabview.tab("Game Chat").grid_columnconfigure(4, weight=1)
        self.tabview.tab("dewrito.json").grid_columnconfigure(4, weight=1)
        self.tabview.tab("FMM").grid_columnconfigure(4, weight=1)
        self.tabview.tab("Crash Fixes").grid_columnconfigure(4, weight=1)
        self.tabview.tab("Experimental").grid_columnconfigure(4, weight=1)


        #Experimental Disclaimer
        self.label = customtkinter.CTkLabel(master=self.tabview.tab("Experimental"), text="These features are experimental and could break your game!", fg_color="transparent")
        self.label.grid(row=0, column=0, pady=(20, 0), padx=20, sticky="nw")


        #DXVK Checkbox
        self.checkbox_DXVK_1 = customtkinter.CTkCheckBox(master=self.tabview.tab("Experimental"))
        self.checkbox_DXVK_1.grid(row=1, column=0, pady=(20, 0), padx=20, sticky="nw")
        self.checkbox_DXVK_1.configure(text="DXVK (If Supported)")
        #self.checkbox_DXVK_1.select()

        self.checkbox_DXVK_2 = customtkinter.CTkCheckBox(master=self.tabview.tab("Experimental"))
        self.checkbox_DXVK_2.grid(row=2, column=0, pady=(20, 0), padx=20, sticky="nw")
        self.checkbox_DXVK_2.configure(text="Build Shader Cache")
        #self.checkbox_DXVK_2.select()

        self.sidebar_button_2 = customtkinter.CTkButton(master=self.tabview.tab("Experimental"), command=self.reset_shaders)
        self.sidebar_button_2.grid(row=3, column=0, pady=(20, 0), padx=20, sticky="nw")
        self.sidebar_button_2.configure(text="Disable Shader Cache")

        # CEF Checkbox
        self.checkbox_CEF_1 = customtkinter.CTkCheckBox(master=self.tabview.tab("Game Chat"))
        self.checkbox_CEF_1.grid(row=0, column=0, pady=(20, 0), padx=20, sticky="n")
        self.checkbox_CEF_1.configure(text="Chat filter and fix chat lag")
        self.checkbox_CEF_1.select()

        # Stats Checkbox
        self.checkbox_STATS_1 = customtkinter.CTkCheckBox(master=self.tabview.tab("dewrito.json"))
        self.checkbox_STATS_1.grid(row=0, column=0, pady=(20, 0), padx=20, sticky="nw")
        self.checkbox_STATS_1.configure(text="Update 'dewrito.json' and add server browser")
        self.checkbox_STATS_1.select()

        #self.checkbox_STATS_3 = customtkinter.CTkCheckBox(master=self.tabview.tab("Stats"))
        #self.checkbox_STATS_3.grid(row=1, column=0, pady=(20, 0), padx=20, sticky="nw")
        #self.checkbox_STATS_3.configure(text="Add Active Master Servers")
        #self.checkbox_STATS_3.select()

        #self.checkbox_STATS_4 = customtkinter.CTkCheckBox(master=self.tabview.tab("Stats"))
        #self.checkbox_STATS_4.grid(row=3, column=0, pady=(20, 0), padx=20, sticky="nw")
        #self.checkbox_STATS_4.configure(text="Add New Server Browser")
        #self.checkbox_STATS_4.select()

        # FMM Checkbox
        self.checkbox_FMM_1 = customtkinter.CTkCheckBox(master=self.tabview.tab("FMM"))
        self.checkbox_FMM_1.grid(row=0, column=0, pady=(20, 0), padx=20, sticky="nw")
        self.checkbox_FMM_1.configure(text="Update FMM")
        self.checkbox_FMM_1.select()

        # Crash Fixes Checkbox
        #self.checkbox_Cfix_1 = customtkinter.CTkCheckBox(master=self.tabview.tab("Crash Fixes"))
        #self.checkbox_Cfix_1.grid(row=0, column=0, pady=(20, 0), padx=20, sticky="nw")
        #self.checkbox_Cfix_1.configure(text="Patch d3d9")
        #self.checkbox_Cfix_1.select()

        self.checkbox_Cfix_2 = customtkinter.CTkCheckBox(master=self.tabview.tab("Crash Fixes"))
        self.checkbox_Cfix_2.grid(row=1, column=0, pady=(20, 0), padx=20, sticky="nw")
        self.checkbox_Cfix_2.configure(text="Update binkw32.dll")
        self.checkbox_Cfix_2.select()

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


                subprocess.Popen(["assets\\update.exe"])
                print("Updated!")
                exit()
        
        else:
            self.log(f"No Updates Found", self.textbox)

            return
    


    #This should be our entry point
    def startup_Tasks(self):
        qolConfig = self.get_config()

        self.log("!!! Backup your ElDewrito folder before updating !!!", self.textbox)


        #if qolConfig["config"]["checkForUpdates"]:
        #    self.log("Checking for updates...", self.textbox)
        #    self.self_update()


    def reset_shaders(self):
        self.log("Select ED Folder", self.textbox)
        file_path = filedialog.askdirectory()
        ed_path = Path(file_path + "/eldorado.exe")

        if ed_path.is_file():
            self.log("Eldorado Found!", self.textbox)

            status, msg = revert_ShaderCache(file_path)

            if status:
                self.log(msg, self.textbox)

            else:
                self.log("Disable shader failed!")
                self.log(msg, self.textbox)

        else:
            self.log("Invalid Game Directory", self.textbox)


    #Grab and validate game directory
    def open_ed_directory(self):
        file_path = filedialog.askdirectory()
        ed_path = Path(file_path + "/eldorado.exe")

        if ed_path.is_file():
            self.log("Eldorado Found!", self.textbox)

            #Check for dewrito_prefs
            status, msg = pre_tasks(file_path)

            if status:
                self.log('Set Game.FirstRun "1"', self.textbox)

            else:
                self.log("Failed to find copy dewrito_prefs or access existing dewrito_prefs.", self.textbox)
                self.log(msg, self.textbox)

            #Get GPU and Vulkan support information
            gpu_support = check_gpu_support()

            for key, value in gpu_support.items():
                self.log(key + ": " + str(value), self.textbox)

            vulkan_Data = get_vulkan_version()

            #Give vulkaninfo enough time to run and 
            time.sleep(3)
            if 'ERROR' in str(vulkan_Data):
                vulkan_Data = '0.0.0'
            
            else:
                self.log("Vulkan Version: " + str(vulkan_Data), self.textbox)

 
            if version.parse(vulkan_Data) > version.parse("1.3.0"):
                self.log("Vulkan Standard Supported!", self.textbox)


                if self.checkbox_DXVK_1.get():
                    status, msg = copy_vulkans(file_path)
                    if status:
                        self.log("Patched for Vulkan Standard ✔️", self.textbox)


                    else:
                        self.log("Failed to copy files for Vulkan", self.textbox)
                        self.log(msg, self.textbox)
  

            elif version.parse(vulkan_Data) > version.parse("1.1.0"):
                self.log("Vulkan Async Supported!")


                if self.checkbox_DXVK_1.get():
                    status, msg = copy_vulkana(file_path)
                    if status:
                        self.log("Patched for Vulkan Async ✔️", self.textbox)


                    else:
                        self.log("Failed to copy files for Vulkan", self.textbox)
                        self.log(msg, self.textbox)


            else:
                self.log("Your machine does not support Vulkan", self.textbox)

            #Add new stats and browser
            if self.checkbox_STATS_1.get():
                status, msg = update_stats(file_path)

                if status:
                    self.log("Updated dewrito.json ✔️", self.textbox)

                else:
                    self.log("Failed to copy new dewrito.json", self.textbox)
                    self.log(msg)
                
                #Update server browser
                status, msg = update_dewcfg(file_path)
                if status:
                    self.log("Browser patched to http://ed6browser.thebeerkeg.net/ ✔️", self.textbox)
            
                else:
                    self.log("Failed to update server browser!", self.textbox)
                    self.log(msg)


            #Copy bink32
            if self.checkbox_Cfix_2.get():
                status, msg = copy_binkw32(file_path)

                if status:
                    self.log("Updated binkw32.dll ✔️", self.textbox)


                else:
                    self.log("Failed to update binkw32.dll", self.textbox)
                    self.log(msg, self.textbox)



            #Copy chat fixes
            if self.checkbox_CEF_1.get():
                status, msg = copy_chat(file_path)

                if status:
                    self.log("Added chat filter and lag fix ✔️", self.textbox)


                else:
                    self.log("Failed to copy chat fixes.", self.textbox)
                    self.log(msg, self.textbox)



            #Update FMM
            if self.checkbox_FMM_1.get():
                status, msg = copy_fmm(file_path)

                if status:
                    self.log(msg, self.textbox)


                else:
                    self.log("Failed to update FMM", self.textbox)
                    self.log(msg, self.textbox)


            #Copy shader tools then generate shader cache
            if self.checkbox_DXVK_2.get():
                status, msg = copy_Update(file_path)

                if status:
                    self.log("Copied shader tools to /maps/update ✔️", self.textbox)


                    self.log("Starting shader gen, go grab a coffee...", self.textbox)
                    self.log("!!! DO NOT CLOSE THE UPDATER !!!", self.textbox)
                    self.log("!!! DO NOT CLOSE THE UPDATER !!!", self.textbox)
                    self.log("!!! DO NOT CLOSE THE UPDATER !!!", self.textbox)
                    

                    status2, msg2 = gen_ShaderCache(file_path)

                    if status2:
                        self.log("Shader generation complete! Your game will lag on first start ✔️", self.textbox)
                        

                    else:
                        self.log("Shader generation failed, please restore cache from backup.", self.textbox)
                        self.log(msg2, self.textbox)


                else:
                    self.log("Failed to copy shader files.", self.textbox)
                    self.log(msg, self.textbox)

            self.log("Done!", self.textbox)

        elif not file_path:
            pass

        else:
            self.log("Invalid Game Directory", self.textbox)


        return



    def open_discord(self):
        webbrowser.open("https://discord.gg/X9DWBgGRMv", new=1)



    def open_fileshare(self):
        webbrowser.open("https://fileshare.zgaf.io", new=1)



    def open_guide(self):
        webbrowser.open("https://bit.ly/eldewritoguide", new=1)



    def verify_files(self):
        #What do we want to verify?
        #Everything in dewrito.json?
        #Updater files?
        file_path = filedialog.askdirectory()
        ed_path = Path(file_path + "/eldorado.exe")

        if ed_path.is_file():
            self.log("Verifying Game Files...", self.textbox)
        
        else:
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

        #Every logging function should end with a task ending message so the user knows if the task has completed. 
        self.log("Done!", self.textbox)



    #Log to our textbox
    def log(self, message, textbox):
        t = time.localtime()
        current_time = time.strftime("%H:%M:%S", t)
        textbox.insert(customtkinter.END, f"[{current_time}] - {message}\n")
        self.textbox.see(customtkinter.END)
        app.update()

        
if __name__ == "__main__":
    app = App()
    app.iconpath = ImageTk.PhotoImage(file=os.path.join("assets","icon.png"))
    app.wm_iconbitmap()
    app.iconphoto(False, app.iconpath)
    pyi_splash.close()
    app.after_idle(app.startup_Tasks)
    app.mainloop()
