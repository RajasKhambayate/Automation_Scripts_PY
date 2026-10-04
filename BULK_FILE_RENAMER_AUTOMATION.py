####################################################################################################

####################################################################################################
# Description: Bulk File Renamer is an automation script that renames hundreds of files at once   ##
# using rules such as prefix , suffix , find-replace , sequential numbering , case change ,       ##
# regex , date stamping and extension change . A preview with conflict detection is always        ##
# shown first and every batch can be undone from the saved rename history .                       ##
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
import re
import json
from datetime import datetime

Separator = "=" * 100
History_File_Name = "rename_history.json"
Max_History = 10

Rule_Names = {
    1 : "Add a prefix",
    2 : "Add a suffix",
    3 : "Find and replace text",
    4 : "Sequential numbering",
    5 : "Change letter case",
    6 : "Clean names (spaces to underscores , remove symbols)",
    7 : "Regex replace",
    8 : "Prepend modified date",
    9 : "Change file extension"
}


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

def ReadText(Message,Allow_Empty) :
    Text = input(Message)

    while (Text == "") and (not Allow_Empty) :
        print("!!This value cannot be empty!!")
        Text = input(Message)

    return Text


class RenameJob :
    def __init__(self,Old_Path,New_Path) :
        self.Old_Path = Old_Path
        self.New_Path = New_Path
        self.Problem = None

    def OldName(self) :
        return os.path.basename(self.Old_Path)

    def NewName(self) :
        return os.path.basename(self.New_Path)


class BulkRenamer :
    def __init__(self) :
        self.Target_Folder = None
        self.Extension_Filter = None
        self.Plan = []
        self.History = []
        self.Renamed_Count = 0

    def SetFolder(self,Folder_Path) :
        if not os.path.isdir(Folder_Path) :
            return False

        self.Target_Folder = os.path.abspath(Folder_Path)
        self.Plan = []
        self.LoadHistory()
        return True

    def SetFilter(self,Extension) :
        if Extension == "" :
            self.Extension_Filter = None
            return

        if not Extension.startswith(".") :
            Extension = "." + Extension

        self.Extension_Filter = Extension.lower()

    def ListFiles(self) :
        Files = []

        for File_Name in sorted(os.listdir(self.Target_Folder)) :
            File_Path = os.path.join(self.Target_Folder,File_Name)

            if not os.path.isfile(File_Path) or File_Name == History_File_Name :
                continue

            if self.Extension_Filter is not None and os.path.splitext(File_Name)[1].lower() != self.Extension_Filter :
                continue

            Files.append(File_Name)

        return Files

    def ApplyRule(self,Rule_Id,Stem,Extension,Index,File_Path,Options) :
        if Rule_Id == 1 :
            Stem = Options["Text"] + Stem

        elif Rule_Id == 2 :
            Stem = Stem + Options["Text"]

        elif Rule_Id == 3 :
            Stem = Stem.replace(Options["Find"],Options["Replace"])

        elif Rule_Id == 4 :
            Number = str(Options["Start"] + Index).zfill(Options["Padding"])
            Stem = Options["Text"] + Number

        elif Rule_Id == 5 :
            if Options["Case"] == "upper" :
                Stem = Stem.upper()
            elif Options["Case"] == "lower" :
                Stem = Stem.lower()
            else :
                Stem = Stem.title()

        elif Rule_Id == 6 :
            Stem = Stem.strip().replace(" ","_")
            Stem = re.sub(r"[^A-Za-z0-9_\-]","",Stem)

        elif Rule_Id == 7 :
            Stem = re.sub(Options["Find"],Options["Replace"],Stem)

        elif Rule_Id == 8 :
            Date_Text = datetime.fromtimestamp(os.path.getmtime(File_Path)).strftime("%Y-%m-%d")
            Stem = Date_Text + "_" + Stem

        elif Rule_Id == 9 :
            Extension = Options["Text"]

        return Stem,Extension

    def BuildPlan(self,Rule_Id,Options) :
        self.Plan = []
        Index = 0

        for File_Name in self.ListFiles() :
            Old_Path = os.path.join(self.Target_Folder,File_Name)
            Stem,Extension = os.path.splitext(File_Name)

            try :
                New_Stem,New_Extension = self.ApplyRule(Rule_Id,Stem,Extension,Index,Old_Path,Options)
            except re.error as Error :
                print("!!Invalid regular expression : " + str(Error) + "!!")
                self.Plan = []
                return 0

            New_Path = os.path.join(self.Target_Folder,New_Stem + New_Extension)

            if New_Path != Old_Path :
                self.Plan.append(RenameJob(Old_Path,New_Path))

            Index += 1

        self.ValidatePlan()
        return len(self.Plan)

    def ValidatePlan(self) :
        Old_Set = set()
        Seen_Targets = {}

        for Job in self.Plan :
            Old_Set.add(Job.Old_Path.lower())

        for Job in self.Plan :
            Target_Key = Job.New_Path.lower()

            if os.path.splitext(Job.NewName())[0].strip() == "" :
                Job.Problem = "Empty new name"
            elif Target_Key in Seen_Targets :
                Job.Problem = "Duplicate of another new name"
            elif os.path.exists(Job.New_Path) and Target_Key not in Old_Set :
                Job.Problem = "A file with this name already exists"

            Seen_Targets[Target_Key] = True

    def HasProblems(self) :
        for Job in self.Plan :
            if Job.Problem is not None :
                return True

        return False

    def DisplayPlan(self) :
        if len(self.Plan) == 0 :
            print("!!No file names would change with this rule!!")
            return

        print("Current Name".ljust(42) + "New Name".ljust(42) + "Status")
        print("-" * 100)

        for Job in self.Plan :
            Status = "OK" if Job.Problem is None else "!! " + Job.Problem
            print(Job.OldName()[:40].ljust(42) + Job.NewName()[:40].ljust(42) + Status)

        print("-" * 100)
        print("Files to rename : " + str(len(self.Plan)))

    def ExecutePlan(self) :
        Batch = []
        Temp_Pairs = []
        Counter = 0

        for Job in self.Plan :
            if Job.Problem is not None :
                continue

            Temp_Path = os.path.join(self.Target_Folder,"__tmp_rename_" + str(Counter) + ".tmp")
            os.rename(Job.Old_Path,Temp_Path)
            Temp_Pairs.append((Temp_Path,Job))
            Counter += 1

        for Temp_Path,Job in Temp_Pairs :
            os.rename(Temp_Path,Job.New_Path)
            Batch.append({"New" : Job.New_Path,"Old" : Job.Old_Path})

        if len(Batch) > 0 :
            self.History.append({"Time" : datetime.now().strftime("%d-%m-%Y %H:%M:%S"),"Renames" : Batch})
            self.History = self.History[-Max_History:]
            self.SaveHistory()

        self.Renamed_Count += len(Batch)
        self.Plan = []
        return len(Batch)

    def SaveHistory(self) :
        History_Path = os.path.join(self.Target_Folder,History_File_Name)

        with open(History_Path,"w") as History_Object :
            json.dump(self.History,History_Object,indent = 4)

    def LoadHistory(self) :
        History_Path = os.path.join(self.Target_Folder,History_File_Name)
        self.History = []

        if not os.path.exists(History_Path) :
            return

        try :
            with open(History_Path,"r") as History_Object :
                self.History = json.load(History_Object)
        except (OSError,ValueError) :
            print("!!Rename history file is damaged and was ignored!!")

    def UndoLast(self) :
        if len(self.History) == 0 :
            return 0

        Batch = self.History.pop()
        Restored = 0
        Temp_Pairs = []
        Counter = 0

        for Entry in Batch["Renames"] :
            if not os.path.exists(Entry["New"]) :
                continue

            Temp_Path = os.path.join(self.Target_Folder,"__tmp_undo_" + str(Counter) + ".tmp")
            os.rename(Entry["New"],Temp_Path)
            Temp_Pairs.append((Temp_Path,Entry["Old"]))
            Counter += 1

        for Temp_Path,Old_Path in Temp_Pairs :
            os.rename(Temp_Path,Old_Path)
            Restored += 1

        self.SaveHistory()
        return Restored

    def Manual(self) :
        print("::::MANUAL FOR BULK FILE RENAMER AUTOMATION::::",end = '\n\n')
        print("Select the folder                    : press 1")
        print("Filter by file extension (optional)  : press 2")
        print("List the files that will be affected : press 3")
        print("Choose a rename rule and apply it    : press 4")
        print("Undo the last rename batch           : press 5")
        print("View rename history                  : press 6")
        print("Exit the application                 : press 7",end = '\n\n')
        print("AVAILABLE RULES")

        for Rule_Id in Rule_Names :
            print("Rule " + str(Rule_Id) + " : " + Rule_Names[Rule_Id])

        print("")
        print("NOTE : a preview is always shown first and nothing is renamed if any name conflicts")
        print("       are found . The last " + str(Max_History) + " batches are remembered in " + History_File_Name)


def CollectOptions(Rule_Id) :
    Options = {}

    if Rule_Id in [1,2] :
        Options["Text"] = ReadText("Enter the text to add : ",False)

    elif Rule_Id == 3 :
        Options["Find"] = ReadText("Enter the text to find : ",False)
        Options["Replace"] = ReadText("Enter the replacement (can be empty) : ",True)

    elif Rule_Id == 4 :
        Options["Text"] = ReadText("Enter the base name (example Holiday_) : ",True)
        Options["Start"] = ReadInteger("Enter the starting number (0 <-> 9999) : ",0,9999)
        Options["Padding"] = ReadInteger("Enter the number of digits (1 <-> 6) : ",1,6)

    elif Rule_Id == 5 :
        print("Press 1 : UPPERCASE   Press 2 : lowercase   Press 3 : Title Case")
        Case_Choice = ReadInteger("Enter the case style : ",1,3)
        Options["Case"] = ["upper","lower","title"][Case_Choice - 1]

    elif Rule_Id == 7 :
        Options["Find"] = ReadText("Enter the regex pattern : ",False)
        Options["Replace"] = ReadText("Enter the replacement (can be empty) : ",True)

    elif Rule_Id == 9 :
        Extension = ReadText("Enter the new extension (example .txt) : ",False)
        Options["Text"] = Extension if Extension.startswith(".") else "." + Extension

    return Options




'''2
====================================================================================================
2'''



'''3
====================================================================================================
3'''


def main() :
    print("Welcome to Rajas's Bulk File Renamer Automation Script")

    Renamer = BulkRenamer()
    Choice = ""

    while True :
        print(Separator)
        print("Current folder : " + str(Renamer.Target_Folder) + "   Filter : " + str(Renamer.Extension_Filter))
        print("For Manual of Application      : Press 0")
        print("To select the folder           : Press 1")
        print("To filter by extension         : Press 2")
        print("To list the affected files     : Press 3")
        print("To choose a rule and rename    : Press 4")
        print("To undo the last rename batch  : Press 5")
        print("To view rename history         : Press 6")
        print("To exit the application        : Press 7")
        Choice = input("Enter your Choice              : ").strip()

        if Choice in ["2","3","4","5","6"] and Renamer.Target_Folder is None :
            print("!!Please select a folder first (Press 1)!!")
            continue

        match Choice :
            case "0" :
                Renamer.Manual()

            case "1" :
                Folder_Path = input("Enter the full path of the folder : ").strip().strip('"')

                if Renamer.SetFolder(Folder_Path) :
                    print("Folder selected : " + Renamer.Target_Folder)
                    print("Rename batches remembered : " + str(len(Renamer.History)))
                else :
                    print("!!That folder does not exist!!")

            case "2" :
                Extension = input("Enter the extension to filter (blank to clear) : ").strip()
                Renamer.SetFilter(Extension)
                print("Filter updated .")

            case "3" :
                Files = Renamer.ListFiles()

                if len(Files) == 0 :
                    print("!!No matching files found!!")
                else :
                    for Counter,File_Name in enumerate(Files,1) :
                        print(str(Counter).rjust(4) + " : " + File_Name)

                    print("Total files : " + str(len(Files)))

            case "4" :
                if len(Renamer.ListFiles()) == 0 :
                    print("!!No matching files found!!")
                    continue

                for Rule_Id in Rule_Names :
                    print("Press " + str(Rule_Id) + " : " + Rule_Names[Rule_Id])

                Rule_Id = ReadInteger("Enter the rule number : ",1,9)
                Options = CollectOptions(Rule_Id)

                Renamer.BuildPlan(Rule_Id,Options)
                Renamer.DisplayPlan()

                if len(Renamer.Plan) == 0 :
                    continue

                if Renamer.HasProblems() :
                    print("!!Conflicts found , rename cancelled . Change the rule and try again!!")
                elif ReadYesNo("Apply these renames ?") :
                    Done = Renamer.ExecutePlan()
                    print(str(Done) + " files renamed successfully .")
                else :
                    print("Rename cancelled .")

            case "5" :
                if len(Renamer.History) == 0 :
                    print("!!Nothing to undo!!")
                elif ReadYesNo("Undo the last rename batch ?") :
                    print(str(Renamer.UndoLast()) + " files restored to their old names .")

            case "6" :
                if len(Renamer.History) == 0 :
                    print("!!No rename history for this folder!!")
                else :
                    for Counter,Batch in enumerate(Renamer.History,1) :
                        print(str(Counter) + " : " + Batch["Time"] + " -> " + str(len(Batch["Renames"])) + " files")

                print("Files renamed in this session : " + str(Renamer.Renamed_Count))

            case "7" :
                print("GoodBye's from the Rajas's Bulk File Renamer Automation Script")
                break

            case _ :
                print("!!Invalid Choice!!")

if __name__ == "__main__" :
    main()


'''3
====================================================================================================
3'''
