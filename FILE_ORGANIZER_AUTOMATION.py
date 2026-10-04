####################################################################################################

####################################################################################################
# Description: File Organizer is an automation script that scans a messy folder and sorts every   ##
# file into neat sub-folders , either by file type or by modified month . It previews the plan    ##
# before moving , keeps a JSON log so the last run can be undone , and can find and delete        ##
# duplicate files using size and MD5 hash comparison .                                            ##
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
import shutil
import hashlib
from datetime import datetime

Separator = "=" * 100
Log_File_Name = "organizer_log.json"
Other_Folder = "Others"

Category_Map = {
    "Images"     : [".jpg",".jpeg",".png",".gif",".bmp",".svg",".webp"],
    "Documents"  : [".pdf",".doc",".docx",".txt",".odt",".rtf",".md"],
    "Sheets"     : [".xls",".xlsx",".csv",".ods"],
    "Slides"     : [".ppt",".pptx",".odp"],
    "Videos"     : [".mp4",".mkv",".avi",".mov",".wmv"],
    "Audio"      : [".mp3",".wav",".flac",".aac",".ogg"],
    "Archives"   : [".zip",".rar",".7z",".tar",".gz"],
    "Code"       : [".py",".c",".cpp",".java",".js",".html",".css",".json"],
    "Installers" : [".exe",".msi",".dmg",".deb"]
}


def FormatSize(Size_In_Bytes) :
    Size = float(Size_In_Bytes)

    for Unit in ["B","KB","MB","GB"] :
        if Size < 1024.0 :
            return str(round(Size,2)) + " " + Unit

        Size = Size / 1024.0

    return str(round(Size,2)) + " TB"

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


class MoveRecord :
    def __init__(self,Source,Destination,Category) :
        self.Source = Source
        self.Destination = Destination
        self.Category = Category
        self.Size = 0


class FileOrganizer :
    def __init__(self) :
        self.Target_Folder = None
        self.Mode = 1
        self.Plan = []
        self.Last_Run = []
        self.Moved_Count = 0
        self.Skipped_Count = 0
        self.Run_Count = 0
        self.Category_Stats = {}

    def SetFolder(self,Folder_Path) :
        if not os.path.isdir(Folder_Path) :
            return False

        self.Target_Folder = os.path.abspath(Folder_Path)
        self.Plan = []
        self.Last_Run = []
        return True

    def GetCategory(self,File_Name) :
        Extension = os.path.splitext(File_Name)[1].lower()

        for Category in Category_Map :
            if Extension in Category_Map[Category] :
                return Category

        return Other_Folder

    def GetMonthFolder(self,File_Path) :
        Modified_Time = os.path.getmtime(File_Path)
        return datetime.fromtimestamp(Modified_Time).strftime("%Y-%m")

    def ResolveCollision(self,Destination) :
        if not os.path.exists(Destination) :
            return Destination

        Base,Extension = os.path.splitext(Destination)
        Counter = 1

        while os.path.exists(Base + "_" + str(Counter) + Extension) :
            Counter += 1

        return Base + "_" + str(Counter) + Extension

    def BuildPlan(self) :
        self.Plan = []
        self.Skipped_Count = 0

        for File_Name in sorted(os.listdir(self.Target_Folder)) :
            Source = os.path.join(self.Target_Folder,File_Name)

            if os.path.isdir(Source) or File_Name == Log_File_Name or File_Name.startswith(".") :
                self.Skipped_Count += 1
                continue

            if self.Mode == 1 :
                Category = self.GetCategory(File_Name)
            else :
                Category = self.GetMonthFolder(Source)

            Destination = os.path.join(self.Target_Folder,Category,File_Name)
            Destination = self.ResolveCollision(Destination)

            Record = MoveRecord(Source,Destination,Category)
            Record.Size = os.path.getsize(Source)
            self.Plan.append(Record)

        return len(self.Plan)

    def DisplayPlan(self) :
        if len(self.Plan) == 0 :
            print("!!Nothing to organize in this folder!!")
            return

        Total_Size = 0

        print("Source File".ljust(40) + "Destination Folder".ljust(22) + "Size")
        print("-" * 75)

        for Record in self.Plan :
            Name = os.path.basename(Record.Source)

            if len(Name) > 37 :
                Name = Name[:34] + "..."

            print(Name.ljust(40) + Record.Category.ljust(22) + FormatSize(Record.Size))
            Total_Size += Record.Size

        print("-" * 75)
        print("Total files : " + str(len(self.Plan)) + "   Total size : " + FormatSize(Total_Size))
        print("Skipped items (folders / hidden / log) : " + str(self.Skipped_Count))

    def ExecutePlan(self) :
        self.Last_Run = []
        self.Moved_Count = 0

        for Record in self.Plan :
            try :
                os.makedirs(os.path.dirname(Record.Destination),exist_ok = True)
                shutil.move(Record.Source,Record.Destination)

                self.Last_Run.append(Record)
                self.Moved_Count += 1
                self.Category_Stats[Record.Category] = self.Category_Stats.get(Record.Category,0) + 1
            except (OSError,shutil.Error) as Error :
                print("!!Could not move " + os.path.basename(Record.Source) + " : " + str(Error) + "!!")
                self.Skipped_Count += 1

        self.Plan = []
        self.Run_Count += 1
        self.SaveLog()

        return self.Moved_Count

    def SaveLog(self) :
        Log_Path = os.path.join(self.Target_Folder,Log_File_Name)
        Entries = []

        for Record in self.Last_Run :
            Entries.append({"Source" : Record.Source,"Destination" : Record.Destination,"Category" : Record.Category})

        Log_Data = {"Time" : datetime.now().strftime("%d-%m-%Y %H:%M:%S"),"Moves" : Entries}

        with open(Log_Path,"w") as Log_Object :
            json.dump(Log_Data,Log_Object,indent = 4)

    def LoadLog(self) :
        Log_Path = os.path.join(self.Target_Folder,Log_File_Name)

        if not os.path.exists(Log_Path) :
            return False

        with open(Log_Path,"r") as Log_Object :
            Log_Data = json.load(Log_Object)

        self.Last_Run = []

        for Entry in Log_Data["Moves"] :
            Record = MoveRecord(Entry["Source"],Entry["Destination"],Entry["Category"])
            self.Last_Run.append(Record)

        return True

    def UndoLastRun(self) :
        if len(self.Last_Run) == 0 :
            self.LoadLog()

        if len(self.Last_Run) == 0 :
            return 0

        Restored = 0

        for Record in reversed(self.Last_Run) :
            if os.path.exists(Record.Destination) :
                Original_Path = self.ResolveCollision(Record.Source)
                shutil.move(Record.Destination,Original_Path)
                Restored += 1

        self.RemoveEmptyFolders()
        self.Last_Run = []

        Log_Path = os.path.join(self.Target_Folder,Log_File_Name)

        if os.path.exists(Log_Path) :
            os.remove(Log_Path)

        return Restored

    def RemoveEmptyFolders(self) :
        Removed = 0

        for Item in os.listdir(self.Target_Folder) :
            Item_Path = os.path.join(self.Target_Folder,Item)

            if os.path.isdir(Item_Path) and len(os.listdir(Item_Path)) == 0 :
                os.rmdir(Item_Path)
                Removed += 1

        return Removed

    def FileHash(self,File_Path) :
        Hasher = hashlib.md5()

        with open(File_Path,"rb") as File_Object :
            Chunk = File_Object.read(65536)

            while Chunk :
                Hasher.update(Chunk)
                Chunk = File_Object.read(65536)

        return Hasher.hexdigest()

    def FindDuplicates(self) :
        Size_Groups = {}
        Hash_Groups = {}

        for Root,Folders,Files in os.walk(self.Target_Folder) :
            for File_Name in Files :
                if File_Name == Log_File_Name :
                    continue

                File_Path = os.path.join(Root,File_Name)
                Size_Groups.setdefault(os.path.getsize(File_Path),[]).append(File_Path)

        for Size in Size_Groups :
            if len(Size_Groups[Size]) < 2 :
                continue

            for File_Path in Size_Groups[Size] :
                Hash_Groups.setdefault(self.FileHash(File_Path),[]).append(File_Path)

        Duplicates = {}

        for Key in Hash_Groups :
            if len(Hash_Groups[Key]) > 1 :
                Duplicates[Key] = sorted(Hash_Groups[Key])

        return Duplicates

    def DeleteDuplicates(self,Duplicates) :
        Deleted_Count = 0
        Freed_Bytes = 0

        for Key in Duplicates :
            for File_Path in Duplicates[Key][1:] :
                Freed_Bytes += os.path.getsize(File_Path)
                os.remove(File_Path)
                Deleted_Count += 1

        return Deleted_Count,Freed_Bytes

    def DisplayReport(self) :
        print("Target folder           : " + str(self.Target_Folder))
        print("Organize mode           : " + ("By file type" if self.Mode == 1 else "By modified month"))
        print("Runs in this session    : " + str(self.Run_Count))
        print("Files moved (last run)  : " + str(self.Moved_Count))
        print("Items skipped           : " + str(self.Skipped_Count))

        if len(self.Category_Stats) == 0 :
            print("!!No files have been organized in this session yet!!")
            return

        print("-" * 50)
        print("Category".ljust(25) + "Files moved")

        for Category in sorted(self.Category_Stats) :
            print(Category.ljust(25) + str(self.Category_Stats[Category]))

    def Manual(self) :
        print("::::MANUAL FOR FILE ORGANIZER AUTOMATION::::",end = '\n\n')
        print("Step 1 : Select the target folder          : press 1")
        print("Step 2 : Choose how files are grouped      : press 2")
        print("Step 3 : Preview what will happen          : press 3")
        print("Step 4 : Organize the files                : press 4")
        print("Undo the last organize run                 : press 5")
        print("Find / delete duplicate files              : press 6")
        print("View session report                        : press 7")
        print("Exit the application                       : press 8",end = '\n\n')
        print("NOTE : every organize run writes " + Log_File_Name + " inside the target folder,")
        print("       which is what allows the undo to work even after restarting the program .")




'''2
====================================================================================================
2'''



'''3
====================================================================================================
3'''


def main() :
    print("Welcome to Rajas's File Organizer Automation Script")

    Organizer = FileOrganizer()
    Choice = ""

    while True :
        print(Separator)
        print("Current folder : " + str(Organizer.Target_Folder))
        print("For Manual of Application      : Press 0")
        print("To select target folder        : Press 1")
        print("To choose organize mode        : Press 2")
        print("To preview the organize plan   : Press 3")
        print("To organize the files          : Press 4")
        print("To undo the last run           : Press 5")
        print("To find duplicate files        : Press 6")
        print("To view session report         : Press 7")
        print("To exit the application        : Press 8")
        Choice = input("Enter your Choice              : ").strip()

        if Choice not in ["0","1","8"] and Organizer.Target_Folder is None :
            print("!!Please select a target folder first (Press 1)!!")
            continue

        match Choice :
            case "0" :
                Organizer.Manual()

            case "1" :
                Folder_Path = input("Enter the full path of the folder to organize : ").strip().strip('"')

                if Organizer.SetFolder(Folder_Path) :
                    print("Target folder set to : " + Organizer.Target_Folder)
                else :
                    print("!!That folder does not exist!!")

            case "2" :
                print("Press 1 : Group by file type (Images, Documents, Code ...)")
                print("Press 2 : Group by modified month (2026-10, 2026-09 ...)")
                Organizer.Mode = ReadInteger("Enter the organize mode : ",1,2)
                print("Organize mode updated .")

            case "3" :
                Organizer.BuildPlan()
                Organizer.DisplayPlan()

            case "4" :
                Count = Organizer.BuildPlan()

                if Count == 0 :
                    print("!!Nothing to organize in this folder!!")
                else :
                    Organizer.DisplayPlan()

                    if ReadYesNo("Proceed with moving " + str(Count) + " files ?") :
                        Moved = Organizer.ExecutePlan()
                        print(str(Moved) + " files organized successfully .")
                    else :
                        print("Organize run cancelled .")

            case "5" :
                if ReadYesNo("Undo the last organize run ?") :
                    Restored = Organizer.UndoLastRun()

                    if Restored == 0 :
                        print("!!No previous run found to undo!!")
                    else :
                        print(str(Restored) + " files restored to their original place .")

            case "6" :
                print("Scanning for duplicate files , please wait . . .")
                Duplicates = Organizer.FindDuplicates()

                if len(Duplicates) == 0 :
                    print("No duplicate files found .")
                else :
                    Group_Number = 1

                    for Key in Duplicates :
                        print("Duplicate group " + str(Group_Number) + " :")

                        for File_Path in Duplicates[Key] :
                            print("    " + File_Path)

                        Group_Number += 1

                    if ReadYesNo("Delete all copies except the first one in every group ?") :
                        Deleted,Freed = Organizer.DeleteDuplicates(Duplicates)
                        print(str(Deleted) + " duplicates deleted , " + FormatSize(Freed) + " freed .")

            case "7" :
                Organizer.DisplayReport()

            case "8" :
                print("GoodBye's from the Rajas's File Organizer Automation Script")
                break

            case _ :
                print("!!Invalid Choice!!")

if __name__ == "__main__" :
    main()


'''3
====================================================================================================
3'''
