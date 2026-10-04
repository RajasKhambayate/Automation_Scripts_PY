####################################################################################################

####################################################################################################
# Description: Gmail Spam and Bin Cleaner is an automation script that logs in to a Gmail account ##
# over IMAP using an App Password and permanently deletes the messages in the Spam and Bin        ##
# (Trash) folders . It shows message counts and a preview first , asks for a typed confirmation   ##
# before deleting , can limit deletion to messages older than N days , and works in safe batches .##
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



import re
import imaplib
import getpass
import email
from email.header import decode_header,make_header
from datetime import datetime,timedelta

Separator = "=" * 100
Gmail_Host = "imap.gmail.com"
Gmail_Port = 993
Batch_Size = 500
Fallback_Spam = "[Gmail]/Spam"
Fallback_Trash = "[Gmail]/Trash"
Month_Names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]


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

def ConfirmByTyping(Message) :
    print("!!WARNING : " + Message + " This CANNOT be undone !!")
    Answer = input("Type DELETE (in capital letters) to continue : ").strip()

    return Answer == "DELETE"

def FormatImapDate(Date_Value) :
    return str(Date_Value.day).zfill(2) + "-" + Month_Names[Date_Value.month - 1] + "-" + str(Date_Value.year)

def DecodeHeader(Raw_Value) :
    if Raw_Value is None :
        return "(none)"

    try :
        return str(make_header(decode_header(Raw_Value))).replace("\r"," ").replace("\n"," ").strip()
    except (UnicodeDecodeError,LookupError,ValueError) :
        return str(Raw_Value)

def Shorten(Text,Length) :
    if len(Text) > Length :
        return Text[:Length - 3] + "..."

    return Text


class SessionEntry :
    def __init__(self,Folder_Label,Deleted_Count) :
        self.Folder_Label = Folder_Label
        self.Deleted_Count = Deleted_Count
        self.Time = datetime.now().strftime("%H:%M:%S")


class GmailCleaner :
    def __init__(self) :
        self.Connection = None
        self.Email_Address = None
        self.Spam_Folder = None
        self.Trash_Folder = None
        self.Deleted_Total = 0
        self.Session_Log = []

    def IsConnected(self) :
        return self.Connection is not None

    def Connect(self,Address,App_Password) :
        try :
            Connection = imaplib.IMAP4_SSL(Gmail_Host,Gmail_Port)
            Connection.login(Address,App_Password)
        except imaplib.IMAP4.error as Error :
            return False,"Login rejected by Gmail : " + str(Error)
        except OSError as Error :
            return False,"Could not reach Gmail (check your internet connection) : " + str(Error)

        self.Connection = Connection
        self.Email_Address = Address
        self.DetectFolders()
        return True,"Logged in as " + Address

    def Disconnect(self) :
        if self.Connection is None :
            return

        try :
            self.Connection.logout()
        except (imaplib.IMAP4.error,OSError) :
            pass

        self.Connection = None
        self.Email_Address = None

    def DetectFolders(self) :
        self.Spam_Folder = Fallback_Spam
        self.Trash_Folder = Fallback_Trash

        Status,Lines = self.Connection.list()

        if Status != "OK" :
            return

        Pattern = re.compile(r'\((?P<Flags>.*?)\) "(?P<Delimiter>.*)" (?P<Name>.*)')

        for Line in Lines :
            if Line is None :
                continue

            Match_Object = Pattern.match(Line.decode("utf-8","replace"))

            if Match_Object is None :
                continue

            Flags = Match_Object.group("Flags")
            Name = Match_Object.group("Name").strip('"')

            if "\\Junk" in Flags :
                self.Spam_Folder = Name
            elif "\\Trash" in Flags :
                self.Trash_Folder = Name

    def Quote(self,Folder) :
        return '"' + Folder + '"'

    def SelectFolder(self,Folder,Read_Only) :
        if Folder.upper() == "INBOX" :
            raise ValueError("Refusing to touch the INBOX")

        Status,Data = self.Connection.select(self.Quote(Folder),readonly = Read_Only)

        if Status != "OK" :
            return False

        return True

    def SearchUids(self,Folder,Days_Older) :
        if not self.SelectFolder(Folder,True) :
            return None

        if Days_Older is None :
            Status,Data = self.Connection.uid("SEARCH",None,"ALL")
        else :
            Limit_Date = datetime.now() - timedelta(days = Days_Older)
            Status,Data = self.Connection.uid("SEARCH",None,"BEFORE",FormatImapDate(Limit_Date))

        if Status != "OK" or not Data or not Data[0] :
            return []

        return Data[0].split()

    def CountMessages(self,Folder) :
        Uids = self.SearchUids(Folder,None)

        if Uids is None :
            return -1

        return len(Uids)

    def PreviewMessages(self,Folder,Limit) :
        Uids = self.SearchUids(Folder,None)

        if Uids is None :
            return None

        Newest = Uids[-Limit:]
        Newest.reverse()
        Previews = []

        for Uid in Newest :
            Status,Data = self.Connection.uid("FETCH",Uid,"(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")

            if Status != "OK" :
                continue

            for Item in Data :
                if isinstance(Item,tuple) :
                    Message = email.message_from_bytes(Item[1])
                    Previews.append((DecodeHeader(Message["Date"]),DecodeHeader(Message["From"]),DecodeHeader(Message["Subject"])))

        return Previews

    def DisplayPreview(self,Folder,Label,Limit) :
        Previews = self.PreviewMessages(Folder,Limit)

        if Previews is None :
            print("!!Could not open the " + Label + " folder!!")
            return

        if len(Previews) == 0 :
            print("The " + Label + " folder is empty .")
            return

        print("Newest " + str(len(Previews)) + " messages in " + Label + " :")
        print("-" * 100)
        print("From".ljust(34) + "Subject".ljust(46) + "Date")
        print("-" * 100)

        for Date_Text,From_Text,Subject_Text in Previews :
            print(Shorten(From_Text,32).ljust(34) + Shorten(Subject_Text,44).ljust(46) + Shorten(Date_Text,20))

    def DeleteUids(self,Folder,Uids) :
        if not self.SelectFolder(Folder,False) :
            return 0

        Deleted = 0

        for Start in range(0,len(Uids),Batch_Size) :
            Batch = Uids[Start:Start + Batch_Size]
            Uid_Set = b",".join(Batch).decode()

            Status,Data = self.Connection.uid("STORE",Uid_Set,"+FLAGS","(\\Deleted)")

            if Status != "OK" :
                print("!!Gmail refused to flag a batch of messages , stopping!!")
                break

            self.Connection.expunge()
            Deleted += len(Batch)
            print("Progress : " + str(Deleted) + " / " + str(len(Uids)) + " messages deleted")

        self.Connection.close()
        return Deleted

    def CleanFolder(self,Folder,Label,Days_Older) :
        Uids = self.SearchUids(Folder,Days_Older)

        if Uids is None :
            print("!!Could not open the " + Label + " folder!!")
            return 0

        if len(Uids) == 0 :
            print("Nothing to delete in " + Label + " .")
            return 0

        Deleted = self.DeleteUids(Folder,Uids)

        self.Deleted_Total += Deleted
        self.Session_Log.append(SessionEntry(Label,Deleted))
        return Deleted

    def DisplayCounts(self) :
        Spam_Count = self.CountMessages(self.Spam_Folder)
        Trash_Count = self.CountMessages(self.Trash_Folder)

        print("Account                 : " + str(self.Email_Address))
        print("Spam folder             : " + self.Spam_Folder + "  ->  " + (str(Spam_Count) if Spam_Count >= 0 else "unavailable") + " messages")
        print("Bin (Trash) folder      : " + self.Trash_Folder + "  ->  " + (str(Trash_Count) if Trash_Count >= 0 else "unavailable") + " messages")

        return Spam_Count,Trash_Count

    def DisplaySessionReport(self) :
        print("Messages deleted in this session : " + str(self.Deleted_Total))

        if len(self.Session_Log) == 0 :
            print("!!No cleanup has been performed yet!!")
            return

        print("-" * 50)
        print("Time".ljust(12) + "Folder".ljust(25) + "Deleted")

        for Entry in self.Session_Log :
            print(Entry.Time.ljust(12) + Entry.Folder_Label.ljust(25) + str(Entry.Deleted_Count))

    def Manual(self) :
        print("::::MANUAL FOR GMAIL SPAM AND BIN CLEANER AUTOMATION::::",end = '\n\n')
        print("BEFORE YOU START (one time setup)")
        print("1) Turn on 2-Step Verification in your Google Account .")
        print("2) Create an App Password : Google Account -> Security -> App passwords .")
        print("3) Use that 16 character App Password here . Your normal Gmail password will NOT work .",end = '\n\n')
        print("Login to Gmail                       : press 1")
        print("Show message count in Spam and Bin   : press 2")
        print("Preview newest Spam messages         : press 3")
        print("Preview newest Bin messages          : press 4")
        print("Delete ALL Spam                      : press 5")
        print("Delete ALL Bin                       : press 6")
        print("Delete ALL Spam and Bin              : press 7")
        print("Delete only items older than N days  : press 8")
        print("View session report                  : press 9")
        print("Logout and exit                      : press 10",end = '\n\n')
        print("NOTE : only the Spam and Bin folders are ever opened for deleting . The Inbox and all")
        print("       other labels are never touched . Your password is never saved anywhere .")




'''2
====================================================================================================
2'''



'''3
====================================================================================================
3'''


def main() :
    print("Welcome to Rajas's Gmail Spam and Bin Cleaner Automation Script")

    Cleaner = GmailCleaner()
    Choice = ""

    while True :
        print(Separator)
        print("Logged in as : " + str(Cleaner.Email_Address))
        print("For Manual of Application             : Press 0")
        print("To login to Gmail                     : Press 1")
        print("To show Spam and Bin counts           : Press 2")
        print("To preview newest Spam messages       : Press 3")
        print("To preview newest Bin messages        : Press 4")
        print("To delete ALL Spam                    : Press 5")
        print("To delete ALL Bin                     : Press 6")
        print("To delete ALL Spam and Bin            : Press 7")
        print("To delete items older than N days     : Press 8")
        print("To view session report                : Press 9")
        print("To logout and exit                    : Press 10")
        Choice = input("Enter your Choice                     : ").strip()

        if Choice in ["2","3","4","5","6","7","8"] and not Cleaner.IsConnected() :
            print("!!Please login first (Press 1)!!")
            continue

        try :
            match Choice :
                case "0" :
                    Cleaner.Manual()

                case "1" :
                    if Cleaner.IsConnected() :
                        Cleaner.Disconnect()

                    Address = input("Enter your Gmail address            : ").strip()
                    Password = getpass.getpass("Enter your 16 character App Password : ").replace(" ","")

                    print("Connecting to Gmail , please wait . . .")
                    Status,Message = Cleaner.Connect(Address,Password)
                    print(Message if Status else "!!" + Message + "!!")

                case "2" :
                    Cleaner.DisplayCounts()

                case "3" :
                    Limit = ReadInteger("How many messages to preview (1 <-> 50) : ",1,50)
                    Cleaner.DisplayPreview(Cleaner.Spam_Folder,"Spam",Limit)

                case "4" :
                    Limit = ReadInteger("How many messages to preview (1 <-> 50) : ",1,50)
                    Cleaner.DisplayPreview(Cleaner.Trash_Folder,"Bin",Limit)

                case "5" :
                    Spam_Count = Cleaner.CountMessages(Cleaner.Spam_Folder)

                    if Spam_Count <= 0 :
                        print("Spam folder is already empty .")
                    elif ConfirmByTyping(str(Spam_Count) + " Spam messages will be permanently deleted .") :
                        print("Total deleted : " + str(Cleaner.CleanFolder(Cleaner.Spam_Folder,"Spam",None)))
                    else :
                        print("Deletion cancelled .")

                case "6" :
                    Trash_Count = Cleaner.CountMessages(Cleaner.Trash_Folder)

                    if Trash_Count <= 0 :
                        print("Bin is already empty .")
                    elif ConfirmByTyping(str(Trash_Count) + " Bin messages will be permanently deleted .") :
                        print("Total deleted : " + str(Cleaner.CleanFolder(Cleaner.Trash_Folder,"Bin",None)))
                    else :
                        print("Deletion cancelled .")

                case "7" :
                    Spam_Count,Trash_Count = Cleaner.DisplayCounts()

                    if max(Spam_Count,0) + max(Trash_Count,0) == 0 :
                        print("Both folders are already empty .")
                    elif ConfirmByTyping(str(max(Spam_Count,0) + max(Trash_Count,0)) + " messages will be permanently deleted .") :
                        Spam_Deleted = Cleaner.CleanFolder(Cleaner.Spam_Folder,"Spam",None)
                        Trash_Deleted = Cleaner.CleanFolder(Cleaner.Trash_Folder,"Bin",None)
                        print("Total deleted : " + str(Spam_Deleted + Trash_Deleted) + " (Spam " + str(Spam_Deleted) + " , Bin " + str(Trash_Deleted) + ")")
                    else :
                        print("Deletion cancelled .")

                case "8" :
                    Days = ReadInteger("Delete items older than how many days (1 <-> 3650) : ",1,3650)
                    Spam_Old = Cleaner.SearchUids(Cleaner.Spam_Folder,Days)
                    Trash_Old = Cleaner.SearchUids(Cleaner.Trash_Folder,Days)
                    Total_Old = len(Spam_Old or []) + len(Trash_Old or [])

                    print("Older than " + str(Days) + " days : Spam " + str(len(Spam_Old or [])) + " , Bin " + str(len(Trash_Old or [])))

                    if Total_Old == 0 :
                        print("Nothing matches that age .")
                    elif ConfirmByTyping(str(Total_Old) + " messages will be permanently deleted .") :
                        Spam_Deleted = Cleaner.CleanFolder(Cleaner.Spam_Folder,"Spam (older)",Days)
                        Trash_Deleted = Cleaner.CleanFolder(Cleaner.Trash_Folder,"Bin (older)",Days)
                        print("Total deleted : " + str(Spam_Deleted + Trash_Deleted))
                    else :
                        print("Deletion cancelled .")

                case "9" :
                    Cleaner.DisplaySessionReport()

                case "10" :
                    Cleaner.Disconnect()
                    print("GoodBye's from the Rajas's Gmail Spam and Bin Cleaner Automation Script")
                    break

                case _ :
                    print("!!Invalid Choice!!")
        except (imaplib.IMAP4.error,OSError,ValueError) as Error :
            print("!!Gmail operation failed : " + str(Error) + "!!")
            print("!!If the connection dropped , press 1 to login again!!")

if __name__ == "__main__" :
    main()


'''3
====================================================================================================
3'''
