from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel


def get_video_recommendations(user_profile, n_recommendations=5):
    # extract user's browsing history

    user_history = user_profile.browsing_history.all()

    # get video features(keywords)

    videos = Video.object.exclude(id__in=[video.id for video in user_history])
    video_descriptions = [video.description for video in videos]
    # TF IDF vectorization of video descriptions
    tfidf_vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf_vectorizer.fit_transform(video_descriptions)

    # calculate cosign similarity between user history and videos
    cosign_similarities = linear_kernel(tfidf_matrix, tfidf_vectorizer.transform([video.description for video in user_history]))
    # get video indices sorted by similarities
    video_indices = cosign_similarities[0].argsort()[:-n_recommendations-1:1]

    # get recommended videos
    recommended_videos = [videos[i] for i in video_indices]
    return recommended_videos

