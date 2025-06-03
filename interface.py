import textwrap
from dotenv import load_dotenv
import os
import mysql.connector
from openai import OpenAI

# Load secrets
load_dotenv()

db_user = os.getenv("DB_USER")
db_pass = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_name = os.getenv("DB_NAME")
api_key = os.getenv("API_KEY")

# GPT prompt setup
client = OpenAI(api_key=api_key)
create_statements = """
CREATE TABLE `student` (
  `id_num` int unsigned NOT NULL,
  `byu_id` varchar(45) NOT NULL,
  `byu_email` varchar(45) NOT NULL,
  `first_name` varchar(45) NOT NULL,
  `middle_names` varchar(45) DEFAULT NULL,
  `last_name` varchar(45) NOT NULL,
  `preferred_name` varchar(45) DEFAULT NULL,
  `section` enum('Piccolo','Clarinet','Alto Sax','Tenor Sax','Trumpet','French Horn','Trombone','Baritone','Tuba','Drumline','Color Guard') NOT NULL,
  `backup_email` varchar(45) DEFAULT NULL,
  `phone_number` char(13) DEFAULT NULL,
  PRIMARY KEY (`id_num`),
  UNIQUE KEY `student_id_UNIQUE` (`id_num`),
  UNIQUE KEY `byu_id_UNIQUE` (`byu_id`),
  UNIQUE KEY `byu_email_UNIQUE` (`byu_email`)
);
CREATE TABLE `uniform_piece` (
  `item_number` tinyint unsigned NOT NULL,
  `item_type` enum('jacket','blue pants','white pants') NOT NULL,
  `height_inches` int NOT NULL,
  `weight_lbs` int NOT NULL,
  `tuba` tinyint NOT NULL DEFAULT '0',
  `student_id` int unsigned DEFAULT NULL,
  PRIMARY KEY (`item_number`,`item_type`),
  KEY `uniform_renter` (`student_id`),
  CONSTRAINT `uniform_renter` FOREIGN KEY (`student_id`) REFERENCES `student` (`id_num`) ON UPDATE CASCADE
);
CREATE TABLE `parka` (
  `parka_num` tinyint unsigned NOT NULL,
  `size` enum('xs','s','m','l','xl','xxl') NOT NULL,
  `student_id` int unsigned DEFAULT NULL,
  PRIMARY KEY (`parka_num`),
  UNIQUE KEY `parka_num_UNIQUE` (`parka_num`),
  UNIQUE KEY `student_id_UNIQUE` (`student_id`),
  CONSTRAINT `parka_renting_student` FOREIGN KEY (`student_id`) REFERENCES `student` (`id_num`) ON DELETE RESTRICT ON UPDATE CASCADE
);
CREATE TABLE `shako` (
  `shako_num` tinyint unsigned NOT NULL,
  `size` enum('xs','s','m','l','xl') NOT NULL,
  `student_id` int unsigned DEFAULT NULL,
  PRIMARY KEY (`shako_num`),
  UNIQUE KEY `shako_num_UNIQUE` (`shako_num`),
  UNIQUE KEY `student_id_UNIQUE` (`student_id`),
  CONSTRAINT `renting_student` FOREIGN KEY (`student_id`) REFERENCES `student` (`id_num`) ON DELETE RESTRICT ON UPDATE CASCADE
);
CREATE VIEW `all_uniform_pieces` AS
    SELECT `uniform_piece`.`item_type` AS `item_type`,`uniform_piece`.`item_number` AS `item_number`,
           `uniform_piece`.`student_id` AS `student_id` FROM `uniform_piece`
    UNION
    SELECT 'shako' AS `item_type`,`shako`.`shako_num` AS `shako_num`,`shako`.`student_id` AS `student_id` FROM `shako`
    UNION
    SELECT 'parka' AS `item_type`,`parka`.`parka_num` AS `parka_num`,`parka`.`student_id` AS `student_id` FROM `parka`;
"""
instructions = """
You are tasked to generate an SQL query using the table schema above and the request following the '----REQUEST----'
token below. A model request and response are provided following the '----MODEL REQUEST----' and
'----MODEL REQUEST----' tokens, respectively. Follow the demonstrated pattern in generating the response; ensure
the returned statement is only an executable SQL query. If the question is unanswerable, please return the string 
"unanswerable" instead.
"""
model_request = """
----MODEL REQUEST----
What uniform pieces does Barney McFife have rented to him?

"""
model_response = "----MODEL RESPONSE----"
model_response += """
SELECT item_type, item_number, student_id FROM all_uniform_pieces
WHERE student_id IN (SELECT id_num FROM student WHERE first_name = "Barney" AND last_name = "McFife");

"""

# Intro
connection_succeeded = False
with mysql.connector.connect(host=db_host,user=db_user,password=db_pass,database=db_name) as conn:
 with conn.cursor() as executor:
      connection_succeeded = True
      print(textwrap.dedent("""\
            Welcome to the AI powered natural-language interface for the Band Uniforms Database.
            Please note that this interface is experimental, and may make mistakes.
            Please use the more regimented interface for exact queries.
            """))

      while True:
            # Get Input, repeat until EXIT
            question = "----REQUEST----\n" + input("What would you like to find out? Type 'EXIT' (in all caps) to quit.\n")
            if "EXIT" in question:
                  print("Goodbye!")
                  break
            response = client.responses.create(
              model="gpt-4.1",
              input=create_statements + instructions + model_request + model_response + question
            ).output_text

            # query database
            db_result = textwrap.dedent(f"""\
                  A database returned this RESPONSE to an SQL query generated to answer the following REQUEST. 
                  Please present this information as an answer to the REQUEST.
                  {question}
                  
                  ----DATABASE RESPONSE----
                  """)
            error_count = 0
            retry = True
            unanswerable = False
            while retry:
                  retry = False
                  try:
                        if "unanswerable" in response.lower() :
                              unanswerable = True
                              raise Exception()

                        executor.execute(response)
                        db_result += str(executor.fetchall())
                        error_count = 0

                  except Exception as err:
                        if error_count < 3 and not unanswerable:
                              error_count += 1
                              retry = True
                              db_result = textwrap.dedent(f"""\
                                    In response to an SQL query generated in response to the following REQUEST:
                                    {question}
                                    
                                    The database returned the following ERROR:
                                    ----ERROR----
                                    {str(err)}
                                    
                                    The SQL QUERY was the following:
                                    ----QUERY----
                                    {response}
                                    
                                    Please return a new SQL query to answer the question, addressing the error. 
                                    If the question is unanswerable, please return the string "unanswerable" instead.""")

                        else:
                              reason = "SQL queries for information have repeatedly returned errors."
                              if unanswerable:
                                    reason = "Answering was determined impossible."
                              db_result = textwrap.dedent(f"""\
                                    In response to the following REQUEST:
                                    {question}
                                    
                                    {reason}
                                    Please generate a message apologizing to the user that the answer could not be obtained,
                                    and asking them to try rephrasing the question or asking a different one. Do not use the
                                    word 'unanswerable'.""")
                              error_count = 0
                  # Prompt GTP with results
                  response = client.responses.create(
                    model="gpt-4.1",
                    input=db_result
                  ).output_text
            print(response)
if not connection_succeeded:
      print("Database connection failed. Please check the credentials in your '.env' file or try again later.")