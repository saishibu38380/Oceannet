#!/usr/bin/python

boatName=raw_input("Enter Boat Name: ")
cpeIP=raw_input("Enter CPE IP: ")

data={"boatName":boatName,"cpeIP":cpeIP}
print("Validate the configurations")
print(data)
ans=raw_input("Store Data (Y/N): ")
if ans == "Y":
  print("Success")
elif ans == "N":
  print("Config Ignored")
else:
  print("Enter Y or N")
  exit()
