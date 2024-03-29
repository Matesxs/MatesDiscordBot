# Strings separated from code

from features.callable_string import Formatable

class Strings(metaclass=Formatable):
  # Help
  help_description = "Show all message commands and help for them"
  help_name_param_description = "Specify name of command or name of extension as parameter to search help only for thing you want"

  help_commands_list_description = "Show list of all available message commands"

  # System
  system_load_description = "Load unloaded extension"
  system_unable_to_load_cog = "Unable to load `{cog}` extension\n`{e}`"
  system_cog_loaded = "Extension `{extension}` loaded"

  system_unload_description = "Unload loaded extension"
  system_unload_protected_cog = "Unable to unload `{extension}` extension - protected"
  system_unable_to_unload_cog = "Unable to unload `{cog}` extension\n`{e}`"
  system_cog_unloaded = "Extension `{extension}` unloaded"

  system_reload_description = "Reload loaded extension"
  system_unable_to_reload_cog = "Unable to reload `{cog}` extension\n`{e}`"
  system_cog_reloaded = "Extension `{extension}` reloaded"

  system_cog_not_found = "Extension `{extension}` not found in extension folders"

  system_cogs_description = "Show all extensions and their states"

  system_logout_brief = "Turn off bot"

  # Errors
  error_command_syntax_error = "Unknown syntax of command"
  error_unknown_command = "Unknown command - use /help for help"
  error_command_on_cooldown = "This command is on cooldown. Please wait {remaining}s"
  error_missing_permission = "You do not have the permissions to use this command."
  error_missing_role = "You do not have {role} role to use this command"
  error_missing_argument = "Missing {argument} argument of command\n{signature}"
  error_bad_argument = "Some arguments of command missing or wrong, use /help to get more info"
  error_max_concurrency_reached = "Bot is busy, try it later"
  error_no_private_message = "This command can't be used in private channel"
  error_interaction_timeout = "Interaction took more than 3 seconds to be responded to. Try again later."
  error_forbiden = "Bot can't do this action"
  error_blocked_dms = "You have blocked DMs"

  # Common
  common_ping_brief = "Ping a bot and get his reponse times"

  common_uptime_brief = "Show uptime of bot"

  # Weather
  weather_set_place_brief = "Set default weather place"
  weather_set_place_invalid_place = "Place is not valid"
  weather_set_place_set = "Your prefered weather place set to **{place}**"

  weather_unset_place_brief = "Remove default weather place"
  weather_unset_place_not_place_to_remove = "You don't have set place to remove"
  weather_unset_place_removed = "Your preferred weather place was removed"

  weather_request_weather_breif = "Request weather report on specific place on the one set by set place command"
  weather_request_weather_place_not_set = "You didn't specified place or dont have set one"
  weather_request_weather_error = "Invalid place or server error"

  # Admin Tools
  admin_tools_clear_description = "Delete recent messages from channel"
  admin_tools_clear_deleted = "Deleted `{message_number}` messages"

  # Dev Tools
  dev_tools_pull_data_description = "Pull guild data and save to database"
  dev_tools_pull_data_pulling_complete = "**Data pulling completed**"
