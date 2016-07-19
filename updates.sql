UPDATE twitter_entity_resolved
INNER JOIN 
(
    SELECT twitter_id, 
    MAX(tweet_id) maxtweet
    FROM tweets
	GROUP BY twitter_id
) tb ON tb.twitter_id = twitter_entity_resolved.twitter_id
SET twitter_entity_resolved.highest_pulled_tweet_id = tb.maxtweet