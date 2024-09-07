import streamlit as st
import os
from langchain_groq import ChatGroq
from leetcode_scraper import LeetcodeScraper
import pandas as pd

# Function to get the profile data from LeetCode
def get_profile_data(username):
    scraper = LeetcodeScraper()
    profile_data = scraper.scrape_user_profile(username)

    return profile_data

# Function to format profile data for the LLM prompt
def format_userdata(profile_data):
    username = profile_data['userPublicProfile']['matchedUser']['username']
    rank_in_problem_count = profile_data['userPublicProfile']['matchedUser']['profile']['ranking']
    aboutMe = profile_data['userPublicProfile']['matchedUser']['profile']['aboutMe']

    activeYears = profile_data['userProfileCalendar']['matchedUser']['userCalendar']['activeYears']
    streak = profile_data['userProfileCalendar']['matchedUser']['userCalendar']['streak']
    totalActiveDays = profile_data['userProfileCalendar']['matchedUser']['userCalendar']['totalActiveDays']

    total_solved_problems = profile_data['userProblemsSolved']['matchedUser']['submitStatsGlobal']['acSubmissionNum'][0]['count']
    total_solved_problems_easy = profile_data['userProblemsSolved']['matchedUser']['submitStatsGlobal']['acSubmissionNum'][1]['count']
    total_solved_problems_medium = profile_data['userProblemsSolved']['matchedUser']['submitStatsGlobal']['acSubmissionNum'][2]['count']
    total_solved_problems_hard = profile_data['userProblemsSolved']['matchedUser']['submitStatsGlobal']['acSubmissionNum'][3]['count']

    attendedContestsCount = profile_data['userContestRankingInfo']['userContestRanking']['attendedContestsCount']
    rating = profile_data['userContestRankingInfo']['userContestRanking']['rating']
    rating = round(rating)
    global_ranking = profile_data['userContestRankingInfo']['userContestRanking']['globalRanking']

    userdata = f"""
    The username : {username}
    Total problem solved {total_solved_problems}
    No of easy problem solved : {total_solved_problems_easy}
    No of medium problem solved : {total_solved_problems_medium}
    no of hard problem solved : {total_solved_problems_hard}
    activeYears : {activeYears}
    longest streak : {streak} days
    total active days : {totalActiveDays} days
    no of contest attended : {attendedContestsCount}
    contest rating : {rating}
    global ranking in contest : {global_ranking}
    global ranking in problem count : {rank_in_problem_count}
    """
    
    return userdata

# Streamlit app function
def main():
    st.title("LeetCode User Roaster")

    # Get API key for LLM from environment variable
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        st.error("GROQ_API_KEY environment variable is not set. Please set it to use this app.")
        return

    # Create the LLM object
    llm = ChatGroq(
        model="llama-3.1-70b-versatile",
        temperature=0.5,
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

                # Prepare messages for LLM
                messages = [
                    (
                        "system",
                        "You're tasked with roasting a LeetCode user based on their profile data. Use their number of solved problems, difficulty preferences, and any inconsistencies in their submissions. The roast should be savage, hitting on their failures, procrastination habits, and their overconfidence despite lacking in basic algorithmic understanding. You’re allowed to get personal and go all-in, picking apart any small victories they brag about while highlighting their major shortcomings. Be brutal, witty, and sarcastic. Remember, it's purely for educational and experimental purposes, so no need to hold back on the trash talk. use about 50 to 100 words.",
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
