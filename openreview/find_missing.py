#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import openreview
import openreview.api
import pandas as pd
from tqdm import tqdm


def main(username, password, venue, accepted_papers_csv):

    df = pd.read_csv(accepted_papers_csv)
    df = df[df["Accepted To"].isin(["Find", "Main"])]
    accepted_nums = set(df["Paper ID"].tolist())

    try:
        client_acl_v2 = openreview.api.OpenReviewClient(
            baseurl="https://api2.openreview.net", username=username, password=password
        )
    except Exception as e:
        print(f"OpenReview connection refused\n{e}")
        exit()

    try:
        client_acl_v2.get_group(venue)
    except Exception as e:
        print(
            f"Unable to get group for: {venue}\nSee below for the OpenReview API error"
        )
        print(f"Exception: {e}")
        exit()

    submissions = client_acl_v2.get_all_notes(
        content={"venueid": venue}, details="replies"
    )
    if len(submissions) <= 0:
        print(
            "No submissions found. Please double check your venue ID and/or permissions to view the submissions"
        )
    decision_by_forum = {
        s.forum: s for s in submissions if s.content["venueid"]["value"] == venue
    }
    submitted_nums = set()
    for submission in tqdm(submissions):
        if submission.id not in decision_by_forum:
            continue
        submitted_nums.add(submission.number)

    unsubmitted_nums = sorted(accepted_nums - submitted_nums)
    print("The following camera-ready documents have not yet been submitted:")
    for num in unsubmitted_nums:
        print(f"  {num}")

    unsubmitted_df = df[df["Paper ID"].isin(unsubmitted_nums)]
    for _, row in unsubmitted_df.iterrows():
        message_body = f"""
            This email is to notify you that the camera-ready deadline for
            EMNLP 2025 was Friday, September 19. As soon as possible, please 
            submit the final version of: 
            
            Paper {row["Paper ID"]}: "{row["Title"]}"             
            
            Thank you,
            The EMNLP 2025 Publication Chairs
        """
        subject = "OVERDUE: EMNLP 2025 camera-ready submission"
        message = '\n'.join([token.strip() for token in message_body.split('\n')])
        recipients = [f'{args.venue}/Submission{row["Paper ID"]}/Authors']
        invitation = f'{args.venue}/-/Edit'
        
        client_acl_v2.post_message(subject, recipients, message, invitation=invitation)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch papers from an OpenReview venue."
    )
    parser.add_argument("username", type=str, help="OpenReview username.")
    parser.add_argument("password", type=str, help="OpenReview password.")
    parser.add_argument(
        "--venue",
        type=str,
        default="EMNLP/2025/Conference",
        help="OpenReview venue ID, found in the URL https://openreview.net/group?id=<VENUE ID>",
    )
    parser.add_argument(
        "--accepted",
        type=str,
        default="accepted-papers.csv",
        help="'Source of Truth' CSV",
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="If set, downloads all papers in the OpenReview venue.",
    )
    parser.add_argument(
        "--pdfs",
        action="store_true",
        help="If set, downloads PDFs.",
    )
    args = parser.parse_args()
    main(args.username, args.password, args.venue, args.accepted)
