####################################################################################################

####################################################################################################
# Description: Backup Manager is an automation script that compresses a source folder into        ##
# time-stamped zip archives . It supports full and incremental backups , exclude patterns ,       ##
# archive verification , safe restore , and an automatic retention policy that deletes the        ##
# oldest backups . Settings are saved in a JSON configuration file .                              ##
####################################################################################################
# Language: Python                                                                                ##
# Compiler : Python3 PVM                                                                          ##
# IDE: Visual Studio code                                                                         ##
####################################################################################################
# Author/Coder: Rajas Khambayate                                                                  ##
# Date: 4th October 2026                                                                          ##
# Day: Sunday                                                                                     ##
####################################################################################################

####################################################################################################



'''2
====================================================================================================
2'''



import os
import json
import zipfile
import fnmatch
from datetime import datetime

Separator = "=" * 100
Config_File_Name = "backup_config.json"
Config_Path = os.path.join(os.path.dirname(os.path.abspath(__file__)),Config_File_Name)
Default_Excludes = ["*.tmp","*.log","__pycache__","node_modules",".git",".DS_Store"]


def FormatSize(Size_In_Bytes) :
    Size = float(Size_In_Bytes)

    for Unit in ["B","KB","MB","GB"] :
        if Size < 1024.0 :
            return str(round(Size,2)) + " " + Unit

        Size = Size / 1024.0

    return str(round(Size,2)) + " TB"

def FormatTime(Timestamp) :
    if Timestamp == 0 :
        return "Never"

    return datetime.fromtimestamp(Timestamp).strftime("%d-%m-%Y %H:%M:%S")

def ReadInteger(Message,Low,High) :
    Value = None

    while Value is None :
        try :
            Value = int(input(Message))

            if (Value < Low) or (Value > High) :
                print("!!Enter a value between " + str(Low) + " <-> " + str(High) + "!!")
                Value = None
        except ValueError :
            print("!!!Please enter a Integer Value Only!!!")

    return Value

def ReadYesNo(Message) :
    Answer = ""

    while Answer not in ["y","n"] :
        Answer = input(Message + " Yes[Y] or No[N] >>>> ").strip().lower()[:1]

    return Answer == "y"


class BackupEntry :
    def __init__(self,Name,Size,Modified_Time) :
        self.Name = Name
        self.Size = Size
        self.Modified_Time = Modified_Time
        self.Kind = "Incremental" if "_incr_" in Name else "Full"


class BackupManager :
    def __init__(self) :
        self.Source_Folder = None
        self.Backup_Folder = None
        self.Retention_Count = 5
        self.Exclude_Patterns = list(Default_Excludes)
        self.Last_Backup_Time = 0.0
        self.Backups_Created = 0

        self.LoadConfig()

    def SaveConfig(self) :
        Config_Data = {
            "Source_Folder"    : self.Source_Folder,
            "Backup_Folder"    : self.Backup_Folder,
            "Retention_Count"  : self.Retention_Count,
            "Exclude_Patterns" : self.Exclude_Patterns,
            "Last_Backup_Time" : self.Last_Backup_Time
        }

        with open(Config_Path,"w") as Config_Object :
            json.dump(Config_Data,Config_Object,indent = 4)

    def LoadConfig(self) :
        if not os.path.exists(Config_Path) :
            return False

        try :
            with open(Config_Path,"r") as Config_Object :
                Config_Data = json.load(Config_Object)
        except (OSError,ValueError) :
            print("!!Saved configuration is damaged , starting with defaults!!")
            return False

        self.Source_Folder = Config_Data.get("Source_Folder")
        self.Backup_Folder = Config_Data.get("Backup_Folder")
        self.Retention_Count = Config_Data.get("Retention_Count",5)
        self.Exclude_Patterns = Config_Data.get("Exclude_Patterns",list(Default_Excludes))
        self.Last_Backup_Time = Config_Data.get("Last_Backup_Time",0.0)
        return True

    def SetSource(self,Folder_Path) :
        if not os.path.isdir(Folder_Path) :
            return False

        self.Source_Folder = os.path.abspath(Folder_Path)
        self.SaveConfig()
        return True

    def SetDestination(self,Folder_Path) :
        try :
            os.makedirs(Folder_Path,exist_ok = True)
        except OSError :
            return False

        self.Backup_Folder = os.path.abspath(Folder_Path)
        self.SaveConfig()
        return True

    def IsReady(self) :
        return (self.Source_Folder is not None) and (self.Backup_Folder is not None)

    def AddExclude(self,Pattern) :
        if Pattern in self.Exclude_Patterns :
            return False

        self.Exclude_Patterns.append(Pattern)
        self.SaveConfig()
        return True

    def RemoveExclude(self,Position) :
        Removed = self.Exclude_Patterns.pop(Position - 1)
        self.SaveConfig()
        return Removed

    def IsExcluded(self,Relative_Path) :
        for Part in Relative_Path.replace("\\","/").split("/") :
            for Pattern in self.Exclude_Patterns :
                if fnmatch.fnmatch(Part,Pattern) :
                    return True

        return False

    def CollectFiles(self,Changed_Only) :
        Collected = []

        for Root,Folders,Files in os.walk(self.Source_Folder) :
            if os.path.abspath(Root).startswith(self.Backup_Folder) :
                Folders[:] = []
                continue

            for File_Name in Files :
                Full_Path = os.path.join(Root,File_Name)
                Relative_Path = os.path.relpath(Full_Path,self.Source_Folder)

                if self.IsExcluded(Relative_Path) :
                    continue

                if Changed_Only and os.path.getmtime(Full_Path) <= self.Last_Backup_Time :
                    continue

                Collected.append((Full_Path,Relative_Path))

        return Collected

    def CreateBackup(self,Changed_Only) :
        Files = self.CollectFiles(Changed_Only)

        if len(Files) == 0 :
            return None,0

        Kind = "incr" if Changed_Only else "full"
        Stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        Archive_Name = "backup_" + Kind + "_" + Stamp + ".zip"
        Archive_Path = os.path.join(self.Backup_Folder,Archive_Name)

        Counter = 0

        with zipfile.ZipFile(Archive_Path,"w",zipfile.ZIP_DEFLATED) as Archive :
            for Full_Path,Relative_Path in Files :
                try :
                    Archive.write(Full_Path,Relative_Path)
                    Counter += 1
                except OSError as Error :
                    print("!!Skipped " + Relative_Path + " : " + str(Error) + "!!")

        self.Last_Backup_Time = datetime.now().timestamp()
        self.Backups_Created += 1
        self.SaveConfig()

        return Archive_Name,Counter

    def ListBackups(self) :
        Entries = []

        if self.Backup_Folder is None :
            return Entries

        for File_Name in os.listdir(self.Backup_Folder) :
            if File_Name.startswith("backup_") and File_Name.endswith(".zip") :
                File_Path = os.path.join(self.Backup_Folder,File_Name)
                Entries.append(BackupEntry(File_Name,os.path.getsize(File_Path),os.path.getmtime(File_Path)))

        Entries.sort(key = lambda Entry : Entry.Modified_Time,reverse = True)
        return Entries

    def DisplayBackups(self) :
        Entries = self.ListBackups()

        if len(Entries) == 0 :
            print("!!No backups found in the backup folder!!")
            return Entries

        print("No.".ljust(6) + "Backup Name".ljust(40) + "Type".ljust(14) + "Size".ljust(14) + "Created")
        print("-" * 95)

        Counter = 1

        for Entry in Entries :
            print(str(Counter).ljust(6) + Entry.Name.ljust(40) + Entry.Kind.ljust(14) + FormatSize(Entry.Size).ljust(14) + FormatTime(Entry.Modified_Time))
            Counter += 1

        return Entries

    def VerifyBackup(self,Archive_Name) :
        Archive_Path = os.path.join(self.Backup_Folder,Archive_Name)

        try :
            with zipfile.ZipFile(Archive_Path,"r") as Archive :
                Bad_File = Archive.testzip()
                Total = len(Archive.namelist())
        except zipfile.BadZipFile :
            return False,"Archive is not a valid zip file"

        if Bad_File is not None :
            return False,"Corrupted entry found : " + Bad_File

        return True,str(Total) + " entries checked , no corruption found"

    def RestoreBackup(self,Archive_Name,Restore_Folder) :
        Archive_Path = os.path.join(self.Backup_Folder,Archive_Name)
        Safe_Root = os.path.realpath(Restore_Folder)
        Restored = 0

        os.makedirs(Restore_Folder,exist_ok = True)

        with zipfile.ZipFile(Archive_Path,"r") as Archive :
            for Member in Archive.namelist() :
                Target_Path = os.path.realpath(os.path.join(Restore_Folder,Member))

                if not Target_Path.startswith(Safe_Root) :
                    print("!!Blocked unsafe path inside archive : " + Member + "!!")
                    continue

                Archive.extract(Member,Restore_Folder)
                Restored += 1

        return Restored

    def DeleteBackup(self,Archive_Name) :
        Archive_Path = os.path.join(self.Backup_Folder,Archive_Name)

        if os.path.exists(Archive_Path) :
            os.remove(Archive_Path)
            return True

        return False

    def ApplyRetention(self) :
        Entries = self.ListBackups()
        Deleted = []

        if len(Entries) <= self.Retention_Count :
            return Deleted

        for Entry in Entries[self.Retention_Count:] :
            if self.DeleteBackup(Entry.Name) :
                Deleted.append(Entry.Name)

        return Deleted

    def DisplaySettings(self) :
        print("Source folder           : " + str(self.Source_Folder))
        print("Backup folder           : " + str(self.Backup_Folder))
        print("Backups to keep         : " + str(self.Retention_Count))
        print("Last backup taken       : " + FormatTime(self.Last_Backup_Time))
        print("Excluded patterns       : " + ", ".join(self.Exclude_Patterns))

    def DisplayStatistics(self) :
        Entries = self.ListBackups()
        Total_Size = 0

        for Entry in Entries :
            Total_Size += Entry.Size

        Full_Count = len([Entry for Entry in Entries if Entry.Kind == "Full"])

        print("Backups stored          : " + str(len(Entries)))
        print("Full backups            : " + str(Full_Count))
        print("Incremental backups     : " + str(len(Entries) - Full_Count))
        print("Total space used        : " + FormatSize(Total_Size))
        print("Created this session    : " + str(self.Backups_Created))

        if len(Entries) > 0 :
            print("Newest backup           : " + Entries[0].Name)
            print("Oldest backup           : " + Entries[-1].Name)

    def Manual(self) :
        print("::::MANUAL FOR BACKUP MANAGER AUTOMATION::::",end = '\n\n')
        print("Set source and backup folders        : press 1")
        print("Take a FULL backup                   : press 2")
        print("Take an INCREMENTAL backup           : press 3  (only files changed since last backup)")
        print("List all backups                     : press 4")
        print("Verify a backup for corruption       : press 5")
        print("Restore a backup into a folder       : press 6")
        print("Change settings (retention/excludes) : press 7")
        print("View statistics                      : press 8")
        print("Exit the application                 : press 9",end = '\n\n')
        print("NOTE : old backups beyond the retention count are removed automatically")
        print("       after every successful backup . Settings are saved in " + Config_File_Name)




'''2
====================================================================================================
2'''



'''3
====================================================================================================
3'''


def main() :
    print("Welcome to Rajas's Backup Manager Automation Script")

    Manager = BackupManager()
    Choice = ""

    while True :
        print(Separator)
        print("For Manual of Application          : Press 0")
        print("To set source and backup folders   : Press 1")
        print("To take a FULL backup              : Press 2")
        print("To take an INCREMENTAL backup      : Press 3")
        print("To list all backups                : Press 4")
        print("To verify a backup                 : Press 5")
        print("To restore a backup                : Press 6")
        print("To change settings                 : Press 7")
        print("To view statistics                 : Press 8")
        print("To exit the application            : Press 9")
        Choice = input("Enter your Choice                  : ").strip()

        if Choice in ["2","3","4","5","6","8"] and not Manager.IsReady() :
            print("!!Please set the source and backup folders first (Press 1)!!")
            continue

        match Choice :
            case "0" :
                Manager.Manual()

            case "1" :
                Source = input("Enter the folder to back up         : ").strip().strip('"')

                if Manager.SetSource(Source) :
                    Destination = input("Enter the folder to store backups in : ").strip().strip('"')

                    if Manager.SetDestination(Destination) :
                        print("Folders saved successfully .")
                    else :
                        print("!!Could not create the backup folder!!")
                else :
                    print("!!Source folder does not exist!!")

            case "2" | "3" :
                Changed_Only = (Choice == "3")
                Name,Count = Manager.CreateBackup(Changed_Only)

                if Name is None :
                    print("!!No files to back up (nothing changed or folder empty)!!")
                else :
                    print("Backup " + Name + " created with " + str(Count) + " files .")
                    Deleted = Manager.ApplyRetention()

                    for Old_Name in Deleted :
                        print("Retention policy removed old backup : " + Old_Name)

            case "4" :
                Manager.DisplayBackups()

            case "5" :
                Entries = Manager.DisplayBackups()

                if len(Entries) > 0 :
                    Number = ReadInteger("Enter the backup number to verify : ",1,len(Entries))
                    Status,Message = Manager.VerifyBackup(Entries[Number - 1].Name)
                    print(("PASSED : " if Status else "FAILED : ") + Message)

            case "6" :
                Entries = Manager.DisplayBackups()

                if len(Entries) > 0 :
                    Number = ReadInteger("Enter the backup number to restore : ",1,len(Entries))
                    Restore_Folder = input("Enter the folder to restore into      : ").strip().strip('"')

                    if ReadYesNo("Restore " + Entries[Number - 1].Name + " into " + Restore_Folder + " ?") :
                        Restored = Manager.RestoreBackup(Entries[Number - 1].Name,Restore_Folder)
                        print(str(Restored) + " files restored .")

            case "7" :
                Manager.DisplaySettings()
                print("Press 1 : Change number of backups to keep")
                print("Press 2 : Add an exclude pattern")
                print("Press 3 : Remove an exclude pattern")
                print("Press 4 : Go back")
                Setting = ReadInteger("Enter your choice : ",1,4)

                if Setting == 1 :
                    Manager.Retention_Count = ReadInteger("Enter number of backups to keep (1 <-> 50) : ",1,50)
                    Manager.SaveConfig()
                    print("Retention updated .")
                elif Setting == 2 :
                    Pattern = input("Enter pattern (example *.mp4 or temp) : ").strip()

                    if Pattern != "" and Manager.AddExclude(Pattern) :
                        print("Pattern added .")
                    else :
                        print("!!Pattern is empty or already present!!")
                elif Setting == 3 and len(Manager.Exclude_Patterns) == 0 :
                    print("!!There are no exclude patterns to remove!!")
                elif Setting == 3 :
                    for Counter,Pattern in enumerate(Manager.Exclude_Patterns,1) :
                        print(str(Counter) + " : " + Pattern)

                    Number = ReadInteger("Enter the pattern number to remove : ",1,len(Manager.Exclude_Patterns))
                    print("Removed pattern : " + Manager.RemoveExclude(Number))

            case "8" :
                Manager.DisplayStatistics()

            case "9" :
                print("GoodBye's from the Rajas's Backup Manager Automation Script")
                break

            case _ :
                print("!!Invalid Choice!!")

if __name__ == "__main__" :
    main()


'''3
====================================================================================================
3'''
