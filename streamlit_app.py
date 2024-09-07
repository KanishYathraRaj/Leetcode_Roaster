import firebase_admin
from firebase_admin import credentials, firestore
from leetcode_scraper import LeetcodeScraper
import streamlit as st
import os
from langchain_groq import ChatGroq
import base64
import json
import datetime

# Function to get the profile data from LeetCode
def get_profile_data(username):
    scraper = LeetcodeScraper()
    profile_data = scraper.scrape_user_profile(username)

    return profile_data

# Function to format profile data for the LLM prompt
def format_userdata(profile_data):
    # Initialize all variables with default values
    username = "N/A"
    rank_in_problem_count = "N/A"
    aboutMe = "N/A"
    activeYears = "N/A"
    streak = "N/A"
    totalActiveDays = "N/A"
    total_solved_problems = "N/A"
    total_solved_problems_easy = "N/A"
    total_solved_problems_medium = "N/A"
    total_solved_problems_hard = "N/A"
    attendedContestsCount = "N/A"
    rating = "N/A"
    global_ranking = "N/A"

    # Check for userPublicProfile and nested matchedUser keys
    if 'userPublicProfile' in profile_data and profile_data['userPublicProfile'] is not None:
        matched_user = profile_data['userPublicProfile'].get('matchedUser', {})
        if matched_user:
            username = matched_user.get('username', 'N/A')
            profile = matched_user.get('profile', {})
            if profile:
                rank_in_problem_count = profile.get('ranking', 'N/A')
                aboutMe = profile.get('aboutMe', 'N/A')

    # Check for userProfileCalendar and nested matchedUser keys
    if 'userProfileCalendar' in profile_data and profile_data['userProfileCalendar'] is not None:
        matched_user_calendar = profile_data['userProfileCalendar'].get('matchedUser', {})
        if matched_user_calendar:
            user_calendar = matched_user_calendar.get('userCalendar', {})
            if user_calendar:
                activeYears = user_calendar.get('activeYears', 'N/A')
                streak = user_calendar.get('streak', 'N/A')
                totalActiveDays = user_calendar.get('totalActiveDays', 'N/A')

    # Check for userProblemsSolved and nested matchedUser keys
    if 'userProblemsSolved' in profile_data and profile_data['userProblemsSolved'] is not None:
        matched_user_solved = profile_data['userProblemsSolved'].get('matchedUser', {})
        if matched_user_solved:
            submit_stats = matched_user_solved.get('submitStatsGlobal', {}).get('acSubmissionNum', [])
            if submit_stats:
                total_solved_problems = submit_stats[0].get('count', 'N/A') if len(submit_stats) > 0 else 'N/A'
                total_solved_problems_easy = submit_stats[1].get('count', 'N/A') if len(submit_stats) > 1 else 'N/A'
                total_solved_problems_medium = submit_stats[2].get('count', 'N/A') if len(submit_stats) > 2 else 'N/A'
                total_solved_problems_hard = submit_stats[3].get('count', 'N/A') if len(submit_stats) > 3 else 'N/A'

    # Check for userContestRankingInfo and nested userContestRanking keys
    if 'userContestRankingInfo' in profile_data and profile_data['userContestRankingInfo'] is not None:
        contest_ranking = profile_data['userContestRankingInfo'].get('userContestRanking', {})
        if contest_ranking:
            attendedContestsCount = contest_ranking.get('attendedContestsCount', 'N/A')
            rating = contest_ranking.get('rating', 'N/A')
            if rating != 'N/A' and rating is not None:
                rating = round(rating)
            global_ranking = contest_ranking.get('globalRanking', 'N/A')

    # Formatted user data for the LLM prompt
    userdata = f"""
    The username : {username} \n
    Total problem solved : {total_solved_problems} \n
    No of easy problems solved : {total_solved_problems_easy} \n
    No of medium problems solved : {total_solved_problems_medium} \n
    No of hard problems solved : {total_solved_problems_hard}
    Active years : {activeYears} \n
    Longest streak : {streak} days \n
    Total active days : {totalActiveDays} days \n
    No of contests attended : {attendedContestsCount} \n
    Contest rating : {rating} \n
    Global ranking in contest : {global_ranking} \n
    Global ranking in problem count : {rank_in_problem_count} \n
    """

    return userdata

def initialize_firebase():
   
    encoded_service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

    # Decode the JSON string back to its original format
    service_account_json = base64.b64decode(encoded_service_account_json).decode()

    # Load the JSON string as a dictionary
    service_account_info = json.loads(service_account_json)

    # Initialize Firebase Admin SDK
    cred = credentials.Certificate(service_account_info)
    
    # Initialize the Firebase app
    try:
        firebase_admin.initialize_app(cred)
    except ValueError:
        # If the app is already initialized, we'll just use it
        pass
    
    # Initialize Firestore
    db = firestore.client()
    return db

# Function to store user input data to Firestore
def store_user_data(username, userdata):
    db = initialize_firebase()
    current_time = datetime.datetime.now()
    doc_ref = db.collection('leetcode_users').document(username)
    doc_ref.set({
        'username': username,
        'profile_data': userdata,
        'timestamp' : current_time
    })
    st.success(f"Be ready to get roasted {username}...")


# Streamlit app function
def main():
    st.title("LeetCode Roaster")

    # Get API key for LLM from environment variable
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        st.error("GROQ_API_KEY environment variable is not set. Please set it to use this app.")
        return

    # Create the LLM object
    llm = ChatGroq(
        model="llama-3.1-70b-versatile",
        temperature=1,
        max_tokens=None,
        timeout=None,
        max_retries=2,
        groq_api_key=api_key
    )

    # Input field for LeetCode username
    username = st.text_input("Enter LeetCode Username:")

    if st.button("Roast Me!"):
        if username:
            try:
                # Get profile data from LeetCode
                profile_data = get_profile_data(username)

                # Format profile data for LLM
                userdata = format_userdata(profile_data)

                # Store the user input data in Firestore
                store_user_data(username, userdata)

                # Prepare messages for LLM
                messages = [
                    (
                        "system",
                        "You're tasked with roasting a LeetCode user based on their profile data. No need to hold back on the trash talk. Roast them heavely so that they wont come back to leetcode again. use about 50 to 100 words.",
                    ),
                    ("human", userdata),
                ]

                # Send to LLM and get response
                ai_msg = llm.invoke(messages)

                # Display the AI-generated response
                st.subheader("LLM Roast")

                st.write(ai_msg.content)
            except Exception as e:
                st.error(f"Error fetching or processing profile data: {e}")
        else:
            st.warning("Please enter a valid LeetCode username.")

if __name__ == "__main__":
    main()
