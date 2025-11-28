# https://github.com/serv0id/skipera
import time
import requests
from loguru import logger
import config


class Watcher(object):
    def __init__(self, session: requests.Session, item: dict, metadata: dict, user_id: str, slug: str, course_id: str):
        self.metadata = metadata
        self.session = session
        self.item = item
        self.slug = slug
        self.user_id = user_id
        self.course_id = course_id

        self.session.headers.update({
            "x-csrf3-token": self.session.cookies["CSRF3-Token"]
        })

    def watch_item(self) -> None:
        if self.metadata["can_skip"]:
            logger.debug("Skippable video!")
            self.start_item()
            time.sleep(2)  # Wait a bit before ending
            self.update_progress()
            self.end_item()
        else:
            self.start_item()
            self.update_progress()
            self.end_item()

    def start_item(self):
        """
        Start watching a video item.
        """
        res = self.session.post(url=f'{config.BASE_URL}opencourse.v1/user/{self.user_id}/course/{self.slug}/'
                                    f'item/{self.item["id"]}/lecture/videoEvents/play?autoEnroll=false',
                                data='{"contentRequestBody":{}}')

        if res.status_code != 200:
            logger.error(f"Couldn't start video {self.item['name']}!")

    def end_item(self):
        """
        End watching a video item.
        Can be called directly for a skippable video.
        """
        res = self.session.post(url=f'{config.BASE_URL}opencourse.v1/user/{self.user_id}/course/{self.slug}/'
                                    f'item/{self.item["id"]}/lecture/videoEvents/ended?autoEnroll=false',
                                data='{"contentRequestBody":{}}')

        if res.status_code != 200:
            logger.error(f"Couldn't end watching {self.item['name']} - Status: {res.status_code}, Response: {res.text}")

    def update_progress(self):
        """
        Updates the watchtime progress of a video.
        """
        video_duration_ms = self.item["timeCommitment"]  # Duration in milliseconds
        video_duration = video_duration_ms / 1000  # Convert to seconds
        
        # Wait 25% of the video duration
        wait_time = video_duration * 0.25
        
        logger.debug(f"Video duration: {video_duration:.0f}s, waiting {wait_time:.0f}s before marking complete")
        
        # First update to show we started watching
        res = self.session.put(url=f'{config.BASE_URL}onDemandVideoProgresses.v1/{self.user_id}~{self.course_id}~'
                                   f'{self.metadata["tracking_id"]}',
                               json={
                                   "videoProgressId": f'{self.user_id}~{self.course_id}~{self.metadata["tracking_id"]}',
                                   "viewedUpTo": int(video_duration_ms * 0.3)  # Mark as 30% watched (in ms)
                               })

        time.sleep(wait_time * 0.3)
        
        # Second update at 70%
        res = self.session.put(url=f'{config.BASE_URL}onDemandVideoProgresses.v1/{self.user_id}~{self.course_id}~'
                                   f'{self.metadata["tracking_id"]}',
                               json={
                                   "videoProgressId": f'{self.user_id}~{self.course_id}~{self.metadata["tracking_id"]}',
                                   "viewedUpTo": int(video_duration_ms * 0.7)  # Mark as 70% watched
                               })
        
        time.sleep(wait_time * 0.3)
        
        # Final update to the full duration
        res = self.session.put(url=f'{config.BASE_URL}onDemandVideoProgresses.v1/{self.user_id}~{self.course_id}~'
                                   f'{self.metadata["tracking_id"]}',
                               json={
                                   "videoProgressId": f'{self.user_id}~{self.course_id}~{self.metadata["tracking_id"]}',
                                   "viewedUpTo": video_duration_ms  # Full duration in ms
                               })

        if res.status_code != 204:
            logger.error(f"Couldn't update progress for {self.item['name']}")
        else:
            time.sleep(wait_time * 0.4)  # Wait the remaining time
