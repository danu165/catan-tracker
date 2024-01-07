import json
import re
import os
from datetime import datetime as dt
from zoneinfo import ZoneInfo

import boto3
import pandas as pd
from apiclient import discovery
from google.auth import aws

SPREADSHEET_ID = "1-o3tpUS70-2iDRfhVVWWNVpEsSBuR0fCdFpU8DJzN_Y"


def validate_message(message_parts):
    errors = []
    score_difference = message_parts[0].strip()
    game_name = message_parts[1].strip().lower()

    if not re.search(r"by \d", score_difference):
        errors.append("The first sentence should follow the format of 'Jess by 5'")

    if "jess" in game_name or "dan" in game_name:
        errors.append("The second sentence should only be the game name")

    if errors:
        error_messages = ". ".join(errors)
        raise Exception(f"The message was not sent in the correct format. {error_messages}")


def convert_message_to_dictionary(received_message):
    # Validate the message parts
    message_parts = received_message.split(".")
    validate_message(message_parts)

    # Transform the message to a dictionary
    now = dt.now(ZoneInfo("America/Los_Angeles"))
    winner, score_difference = message_parts[0].strip().split(" by ")
    my_dict = {
        "Game date": f"{now.month}/{now.day}/{now.year}",
        "Winner": winner,
        "Score difference": score_difference,
        "Game": message_parts[1].strip(),
    }
    if len(message_parts) > 2:
        for message_part in message_parts[2:]:
            stripped_message_part = message_part.strip()
            if stripped_message_part:
                my_dict[f"{stripped_message_part}?"] = "Yes"

    return my_dict


class GoogleSheets:
    """Works with data in Google Sheets and updates the known last row and last column of a dataset as it goes."""

    def __init__(self, credentials_filepath, sheet_name="Sheet1"):
        raw_creds = json.load(open(credentials_filepath))
        credentials = aws.Credentials.from_info(raw_creds)
        scoped_credentials = credentials.with_scopes(["https://www.googleapis.com/auth/spreadsheets"])
        self.service = discovery.build("sheets", "v4", credentials=scoped_credentials).spreadsheets()
        self.sheet_name = sheet_name
        self._get_last_row_and_col()
        self._get_current_columns()

    def _get_last_row_and_col(self):
        # This gets the last row and column by creating an empty table. It uses the range of the empty table
        # to determine the last row and column.
        table = {"majorDimension": "ROWS", "values": []}
        # append the empty table
        request = self.service.values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{self.sheet_name}!A:ZZZ",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body=table,
        )
        result = request.execute()

        # get last row and last column with regex
        p = re.compile("^.*![A-Z]+\d+:([A-Z]+)(\d+)$")
        match = p.match(result["tableRange"])
        last_col = match.group(1)
        last_row = match.group(2)
        self.last_col = last_col
        self.last_row = last_row
        return last_row, last_col

    @staticmethod
    def _excel_column_name(n):
        """Converts a number to an excel column name. IE. 1 => A, 27 => AA, 53 => BA, etc."""

        result = ""
        while n > 0:
            # find the index of the next letter and concatenate the letter to the solution
            # here index 0 corresponds to `A`, and 25 corresponds to `Z`
            index = (n - 1) % 26
            result += chr(index + ord("A"))
            n = (n - 1) // 26

        return result[::-1]

    @staticmethod
    def _excel_column_number(name):
        """Excel-style column name to number, IE. A => 1, Z => 26, AA => 27, BA => 53."""

        n = 0
        for c in name:
            n = n * 26 + 1 + ord(c) - ord("A")
        return n

    def _get_current_columns(self):
        result = self.service.values().get(spreadsheetId=SPREADSHEET_ID, range=f"A1:{self.last_col}1").execute()
        self.columns = result["values"][0]
        return self.columns

    def _update_values(self, range, data):
        params = dict(spreadsheetId=SPREADSHEET_ID, body=data, range=range, valueInputOption="USER_ENTERED")
        self.service.values().update(**params).execute()

    def update_columns(self, data_dict):
        additional_columns = [k for k in data_dict.keys() if k not in self.columns]
        if additional_columns:
            print("We have additional columns!")
            print(additional_columns)

            # Get range that needs to be updated
            current_col_num = self._excel_column_number(self.last_col)
            next_col = self._excel_column_name(current_col_num + 1)
            new_last_col = self._excel_column_name(current_col_num + len(additional_columns))
            new_col_range = f"{next_col}1:{new_last_col}1"

            # Update the values for the range
            data = {"values": [additional_columns]}
            self._update_values(new_col_range, data)

            # Update the recorded last column and column list
            self.last_col = new_last_col
            self.columns += additional_columns

    def add_data(self, data_dict):
        # Get range
        next_row = int(self.last_row) + 1
        range_name = f"{self.sheet_name}!A{next_row}:{self.last_col}{next_row}"

        # Get values
        data_values = []
        for col in self.columns:
            data_values.append(data_dict.get(col))
        data = {"values": [data_values]}
        print("Updating")
        self._update_values(range_name, data)
        self.last_row = next_row

    def get_all_data(self):
        range_name = f"{self.sheet_name}!A2:{self.last_col}{self.last_row}"
        result = self.service.values().get(spreadsheetId=SPREADSHEET_ID, range=range_name).execute()
        return result["values"]


def determine_winner(jess_record, dan_record):
    if jess_record > dan_record:
        return f"Jess is winning {jess_record}-{dan_record}"

    if dan_record > jess_record:
        return f"Dan is winning {dan_record}-{jess_record}"

    return f"it's a tie {jess_record}-{dan_record}"


def build_response(df, df_game, df_all_conditions, winner, game, score_diff, score_diff_wins):
    """
    Builds a message response based on:
        1. The overall record
        2. The record for just the game played
        3. The amount of times the winner has won the game by the same score difference
        4. The record for the current conditions
    """

    # Get all of the records
    overall_records = df["Winner"].value_counts()
    game_records = df_game["Winner"].value_counts()
    conditions_records = df_all_conditions["Winner"].value_counts()
    jess_record, dan_record = overall_records.get("Jess", 0), overall_records.get("Dan", 0)
    jess_game_record, dan_game_record = game_records.get("Jess", 0), game_records.get("Dan", 0)
    jess_conditions_record, dan_conditions_record = conditions_records.get("Jess", 0), conditions_records.get("Dan", 0)

    # Get the winners in a sentence format for the response text message.
    overall_winner = determine_winner(jess_record, dan_record)
    game_type_winner = determine_winner(jess_game_record, dan_game_record)
    conditions_winner = determine_winner(jess_conditions_record, dan_conditions_record)

    str_time = "times" if score_diff_wins > 1 else "time"
    response = (
        f"Congrats {winner}!\n"
        f"Overall, {overall_winner}.\n"
        f"{game_type_winner} in {game}.\n"
        f"{winner} has won by {score_diff} in this game {score_diff_wins} {str_time}.\n"
        f"For all matching conditions, {conditions_winner}."
    )

    return response


def lambda_handler(event, context):
    # Convert message to a dictionary
    print(event)
    sns = boto3.client("sns")
    try:
        received_message = event["Records"][0]["Sns"]["Message"]
        data_dict = convert_message_to_dictionary(received_message)
        print("Converted data")
        print(data_dict)

        # Input data into google sheets
        sheets = GoogleSheets("googlecreds.json")
        sheets.update_columns(data_dict)
        sheets.add_data(data_dict)

        # Get all of the current data
        # Create a filtered dataframe for just the game
        # Create a filtered dataframe for the score difference, winner, and game
        # Create a filtered dataframe for all current conditions. Ignore some columns so that not too much is filtered.
        df = pd.DataFrame(sheets.get_all_data(), columns=sheets.columns)
        game, score_diff, winner = data_dict["Game"], data_dict["Score difference"], data_dict["Winner"]
        df_game = df[df["Game"] == game]
        df_score_and_game = df[(df["Game"] == game) & (df["Score difference"] == score_diff) & (df["Winner"] == winner)]
        ignore_columns = ["Game date", "Winner", "Score difference"]
        query = " & ".join([f'`{k}` == "{v}"' for k, v in data_dict.items() if k not in ignore_columns])
        df_all_conditions = df.query(query)

        # Build and send response
        score_diff_wins = len(df_score_and_game.index)
        response = build_response(df, df_game, df_all_conditions, winner, game, score_diff, score_diff_wins)
    except Exception as e:
        response = f"{e.__class__.__name__}: {e}"
    sns.publish(TopicArn=os.environ["SNS_TOPIC_ARN"], Message=response)
    return response
