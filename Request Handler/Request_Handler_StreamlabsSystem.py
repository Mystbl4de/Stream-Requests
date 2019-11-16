#!/usr/bin/python
# -*- coding: utf-8 -*-

# ---------------------------------------
# Import Libraries
# ---------------------------------------
import clr

clr.AddReference("IronPython.SQLite.dll")
clr.AddReference("IronPython.Modules.dll")

import os
import codecs
import json
import time
import sys

# ---------------------------------------
# Script Information
# ---------------------------------------
ScriptName = "Stream Request Handler"
Website = "https://twitch.tv/mystblade"
Description = "Script to be able to Add and Remove requests and also write and manipulate a file that " \
              "can be displayed on stream!"
Creator = "Mystblade"
Version = "1.0.0.0"

#   Versions
""" Most Recent Release:

1.0.0.0 - Added in all current valid requests - first release woo!!

0.0.3.2 - fixed for multiple word requests.

0.0.3.1 - Updated to use memory rather than write to file.
		created valid request file and populated it.
		optimising some of the commands for twitch.
		got all commands to actually work.

Open README.txt for full changelog and more further info.

"""

# ---------------------------------------
# File Variables
# ---------------------------------------
""" change the .json, or .txt to update / create the file name you wish."""
SettingsFile = os.path.join(os.path.dirname(__file__), "settings.json")
ValidationFile = os.path.join(os.path.dirname(__file__), "ValidationFile.json")
Read_Me = os.path.join(os.path.dirname(__file__), "README.txt")


# ---------------------------------------
# Classes
# ---------------------------------------
class Settings(object):
	""" Load in saved settings file if available else set default values. """

	def __init__(self, settingsfile=None):
		try:
			with codecs.open(settingsfile, encoding="utf-8-sig", mode="r") as f:
				self.__dict__ = json.load(f, encoding="utf-8")
		except:
			self.OnlyLive = False
			self.Command1 = "!tr"
			self.CommandCost = 0
			self.Command2 = "!next5"
			self.Command3 = "!played"
			self.Command4 = "!removetank"
			self.Permission = "Everyone"
			self.PermissionInfo = ""
			self.Usage = "Stream Chat"
			self.CasterCD = True
			self.Cooldown = 5
			self.UserCooldown = 10
			self.UseCD = False
			self.OnUserCooldown = "{0} the command is still on cooldown for {1} seconds!"
			self.BaseResponse = "{0} {1} has requested {2}, {2} has been added to the queue!"
			self.ErrorResponse = "Sorry! {0} {1} The requested {2} has been denied by HQ! Please Check the request and try again!"
			self.NotEnoughResponse = "{0} {1} you do not have enough {2} to request {3}! Gain some more {2} and try again!"
			self.InfoResponse = "To submit your tank request for approval please use !tr <tank>"
			self.PermissionResp = "$user -> only $permission ($permissioninfo) and higher can use this command"

	def Reload(self, jsondata):
		""" Reload settings from AnkhBot user interface by given json data. """
		self.__dict__ = json.loads(jsondata, encoding="utf-8")
		return

	def Save(self, settingsfile):
		""" Save settings contained within to .json and .js settings files. """
		try:
			with codecs.open(settingsfile, encoding="utf-8-sig", mode="w+") as f:
				json.dump(self.__dict__, f, encoding="utf-8", ensure_ascii=False)
			with codecs.open(settingsfile.replace("json", "js"), encoding="utf-8-sig", mode="w+") as f:
				f.write("var settings = {0};".format(json.dumps(self.__dict__, encoding='utf-8', ensure_ascii=False)))
		except:
			Parent.Log(ScriptName, "Failed to save settings to file.")
		return


# ---------------------------------------
# Validation List
# ---------------------------------------
def Validation_List():
	try:
		with codecs.open(ValidationFile, encoding="utf-8-sig", mode="r") as f:
			Valid_List = json.load(f, encoding="utf-8")
			Parent.Log(ScriptName, "Return Valid_List ok!")
			return Valid_List
	except:
		Parent.Log(ScriptName, "Failed to open Validation List")
	return {}

# ---------------------------------------
# Initialize Data on Load
# ---------------------------------------
def Init():
	# Globals
	global ScriptSettings
	global commands
	global request_list
	global ValidRequests
	global Common_Names
	global vlist

	# Load in saved settings
	ScriptSettings = Settings(SettingsFile)

	# Request List
	request_list = []
	vlist = Validation_List()
	ValidRequests = vlist["ValidRequest"]
	Common_Names = vlist["Common_Names"]

	# List of Commands
	commands = [
		ScriptSettings.Command1,
		ScriptSettings.Command2,
		ScriptSettings.Command3,
		ScriptSettings.Command4
	]

	# End of Init
	return


# ---------------------------------------
# Reload Settings on Save
# ---------------------------------------
def ReloadSettings(jsondata):
	# Globals
	global ScriptSettings

	# Reload newly saved settings
	ScriptSettings.Reload(jsondata)

	# End of ReloadSettings
	return


# ---------------------------------------
#	Script is going to be unloaded
# ---------------------------------------
def Unload():
	# Save changed settings on unload
	ScriptSettings.Save(SettingsFile)

	# End of Unload
	return


# ---------------------------------------
#	Script is enabled or disabled on UI
# ---------------------------------------
def ScriptToggled(state):
	# Globals
	global ScriptSettings

	# Upon disabled (toggled off)
	if not state:
		# Even though script stays in memory
		# but the execute and tick are not called
		# we just save here to demonstrate this
		ScriptSettings.Save(SettingsFile)

	# End of Unload
	return


# ---------------------------------------
# Execute
# ---------------------------------------
def Execute(data):
	""" Required Execute data Function"""
	global commands
	if data.IsChatMessage():
		Parent.Log(ScriptName, "Data is Chat msg")
		if not IsFromValidSource(data, ScriptSettings.Usage):
			Parent.Log(ScriptName, "Is Valid Source")
			return

		if not HasPermission(data):
			Parent.Log(ScriptName, "Has Permission")
			return

		if IsOnCooldown(data):
			Parent.Log(ScriptName, "Not on Cool down")
			return

		if ScriptSettings.OnlyLive and Parent.IsLive() is False:
			Parent.Log(ScriptName, "Check live called")
			return

		Parent.Log(ScriptName, "Executed RunCommand")
		RunCommand(data)


# ---------------------------------------
# [Optional] Functions
# ---------------------------------------
def SendResp(data, Usage, Message):
	Parent.Log(ScriptName, "SendResp called")
	"""Sends message to Stream or discord chat depending on settings"""
	Message = Message.replace("$user", data.UserName)
	Message = Message.replace("$currencyname", Parent.GetCurrencyName())
	Message = Message.replace("$target", data.GetParam(1))
	Message = Message.replace("$permissioninfo", ScriptSettings.PermissionInfo)
	Message = Message.replace("$permission", ScriptSettings.Permission)

	l = ["Stream Chat", "Chat Both", "All", "Stream Both"]
	if not data.IsFromDiscord() and (Usage in l) and not data.IsWhisper():
		Parent.SendStreamMessage(Message)

	l = ["Stream Whisper", "Whisper Both", "All", "Stream Both"]
	if not data.IsFromDiscord() and data.IsWhisper() and (Usage in l):
		Parent.SendStreamWhisper(data.User, Message)

	l = ["Discord Chat", "Chat Both", "All", "Discord Both"]
	if data.IsFromDiscord() and not data.IsWhisper() and (Usage in l):
		Parent.SendDiscordMessage(Message)

	l = ["Discord Whisper", "Whisper Both", "All", "Discord Both"]
	if data.IsFromDiscord() and data.IsWhisper() and (Usage in l):
		Parent.SendDiscordDM(data.User, Message)


def IsFromValidSource(data, Usage):
	"""Return true or false depending on the message is sent from
	a source that's in the usage setting or not"""
	if not data.IsFromDiscord():
		l = ["Stream Chat", "Chat Both", "All", "Stream Both"]
		if not data.IsWhisper() and (Usage in l):
			return True

		l = ["Stream Whisper", "Whisper Both", "All", "Stream Both"]
		if data.IsWhisper() and (Usage in l):
			return True

	if data.IsFromDiscord():
		l = ["Discord Chat", "Chat Both", "All", "Discord Both"]
		if not data.IsWhisper() and (Usage in l):
			return True

		l = ["Discord Whisper", "Whisper Both", "All", "Discord Both"]
		if data.IsWhisper() and (Usage in l):
			return True
	return False


def ReportBug():
	"""Open google form to report a bug"""
	os.system("explorer http://bit.ly/2ZNujxQ")


def OpenReadMe():
	os.startfile(Read_Me)


def RunCommand(data):
	Parent.Log(ScriptName, "RunCommand called")
	"""Execute the command if triggered"""
	# template for commands <param 0 > <param 1:> == <!command> <option>
	command = data.GetParam(0)
	option = " ".join(data.Message.split()[1:])

	if command == commands[0]:
		Parent.Log(ScriptName, "Called New_Request")
		new_request(data, option)
		return

	elif command == commands[1]:
		Parent.Log(ScriptName, "Called Next Five")
		next_five(data, request_list)
		return

	elif command == commands[2]:
		Parent.Log(ScriptName, "Called Played")
		played(data, request_list)
		return

	elif command == commands[3]:
		Parent.Log(ScriptName, "Called Remove")
		remove(data, option, request_list)
	# refresh the file

	if Parent.HasPermission(data.User, "Caster", "") and ScriptSettings.CasterCD:
		return

	Parent.AddUserCooldown(ScriptName, ScriptSettings.Command1, data.User, ScriptSettings.UserCooldown)
	Parent.AddCooldown(ScriptName, ScriptSettings.Command1, ScriptSettings.Cooldown)


def AddCooldown(data):
	Parent.Log(ScriptName, "Add Cooldown")
	"""add cooldowns"""
	if Parent.HasPermission(data.User, "Caster", "") and ScriptSettings.CasterCD:
		Parent.AddCooldown(ScriptName, ScriptSettings.Command, ScriptSettings.Cooldown)
		return

	else:
		Parent.AddUserCooldown(ScriptName, ScriptSettings.Command, data.User, ScriptSettings.UserCooldown)
		Parent.AddCooldown(ScriptName, ScriptSettings.Command, ScriptSettings.Cooldown)


def IsOnCooldown(data):
	Parent.Log(ScriptName, "Check cooldown")
	"""Return true if command is on cooldown and send cooldown message if enabled"""
	Cooldown = Parent.IsOnCooldown(ScriptName, data.GetParam(0))
	UserCooldown = Parent.IsOnUserCooldown(ScriptName, data.GetParam(0), data.User)
	caster = (Parent.HasPermission(data.User, "Caster", "") and ScriptSettings.CasterCD)

	if (Cooldown or UserCooldown) and caster is False:

		if ScriptSettings.UseCD:
			cooldownDuration = Parent.GetCooldownDuration(ScriptName, ScriptSettings.Command)
			userCDD = Parent.GetUserCooldownDuration(ScriptName, ScriptSettings.Command, data.User)

			if cooldownDuration > userCDD:
				m_CooldownRemaining = cooldownDuration

				message = ScriptSettings.OnCooldown.format(data.UserName, m_CooldownRemaining)
				SendResp(data, ScriptSettings.Usage, message)

			else:
				m_CooldownRemaining = userCDD

				message = ScriptSettings.OnUserCooldown.format(data.UserName, m_CooldownRemaining)
				SendResp(data, ScriptSettings.Usage, message)
		return True
	return False


def HasPermission(data):
	"""Returns true if user has permission and false if user doesn't"""
	Parent.Log(ScriptName, "Has Permission called")
	if not Parent.HasPermission(data.User, ScriptSettings.Permission, ScriptSettings.PermissionInfo):
		message = ScriptSettings.PermissionResp.format(data.UserName, ScriptSettings.Permission,
		                                               ScriptSettings.PermissionInfo)
		SendResp(data, ScriptSettings.Usage, message)
		Parent.Log(ScriptName, "Has Perms: Return False")
		return False
	Parent.Log(ScriptName, "Has Perms: Return True")
	return True


# ---------------------------------------
# append Tank to list.
# ---------------------------------------

# self.BaseResponse = "{0} {1} has requested {2}, {2} has been added to the queue!"
# self.ErrorResponse = "Sorry! {0} {1} has requested {2}, Please Check the request and try again!"
# NotEnoughResponse = "{0} {1} you do not have enough {2} to request {3}! Gain some more {2} and try again!"

def new_request(data, requested):
	Parent.Log(ScriptName, "New Req called (req=%s, valid=%s)" % (requested, ValidRequests))
	if requested in Common_Names:
		requested = Common_Names[requested]
	if requested in ValidRequests:
		if Parent.RemovePoints(data.User, data.UserName, ScriptSettings.CommandCost):
			Parent.Log(ScriptName, "Removed Currency")
			message = ScriptSettings.BaseResponse.format(Parent.GetRank(data.UserName),
		                                                   data.UserName,
		                                                   requested
		                                                   )
			SendResp(data, ScriptSettings.Usage, message)
			request_list.append(requested)
			Parent.BroadcastWsEvent("NEW", json.dumps(request_list))

		else:
			Parent.Log(ScriptName, "No Currency")
			no_money = ScriptSettings.NotEnoughResponse.format(Parent.GetRank(data.UserName),
			                                                   data.UserName,
			                                                   Parent.GetCurrencyName(),
			                                                   data.GetParam(1)
			                                                   )
			SendResp(data, ScriptSettings.Usage, no_money)

	else:
		error_message = ScriptSettings.ErrorResponse.format(Parent.GetRank(data.UserName),
		                                                    data.UserName,
		                                                    data.GetParam(1).upper()
		                                                    )
		SendResp(data, ScriptSettings.Usage, error_message)
		Parent.Log(ScriptName, "not in Validation List called")


# ---------------------------------------
# List Length to max of 5.
# ---------------------------------------
def next_five(data, list):
	list_length = set_max(len(list))
	response1 = ""
	response1 = response1 + "There is %d request(s) in the queue! Next %d up" % (len(list), list_length)
	for tank in range(set_max(len(list))):
		response1 = response1 + "! " + list[tank].upper()

	SendResp(data, ScriptSettings.Usage, response1)

# ---------------------------------------
# Next 5 Requests.
# ---------------------------------------
# Code to limit to 5 max
def set_max(list):
	if list > 5:
		return 5
	else:
		return list


# ---------------------------------------
# Delete Played tanks from list.
# ---------------------------------------
def played(data, list):
	#del list[0]
	played = list.pop(0)
	next = list[0]
	SendResp(data, ScriptSettings.Usage, Parent.GetChannelName() + " just played the " + played + "! next up is the "
	         + next +"!")
	Parent.BroadcastWsEvent("NEW", json.dumps(request_list))
	Parent.Log(ScriptName, "new tank list called")


# ---------------------------------------
# removing selected Tank from list.
# ---------------------------------------
def remove(data, requested, list):
	requested = list.pop(int(requested) - 1)
	Parent.BroadcastWsEvent("NEW", json.dumps(request_list))
	SendResp(data, ScriptSettings.Usage, requested + " has been removed from the queue!")


# ---------------------------------------
# Tick
# ---------------------------------------
def Tick():

	"""
		Tick is a required function and will be called every time the program progresses.
		This can be used for example to create simple timer if you want to do let the
		script do something on a timed basis.This function will _not_ be called	when the
		user disabled the script	with the switch on the user interface.
	"""

	return


# ---------------------------------------
# SetDefaults Custom User Interface Button
# ---------------------------------------
def SetDefaults():

	# Globals
	global ScriptSettings

	# Set defaults by not supplying a settings file
	ScriptSettings = Settings()

	# Save defaults back to file
	ScriptSettings.Save(SettingsFile)

	# End of SetDefaults
	return
