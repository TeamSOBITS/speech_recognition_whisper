import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool
import os
import glob
import time
import threading
import whisper
from ament_index_python.packages import get_package_share_directory
import json

class WIPTranscriber(Node):
    def __init__(self):
        super().__init__('wip_transcriber_node')
        share_dir = get_package_share_directory('speech_recognition_whisper')
        self.audio_dir = os.path.join(os.path.abspath(os.path.join(share_dir, '..', '..', '..', '..')),
                                      'src', 'speech_recognition_whisper', 'sound_file')

        self.declare_parameter('model_name', 'base')
        self.declare_parameter('language', 'en')
        self.declare_parameter('replace_prompt_whisper', [""])
        self.declare_parameter('task', 'transcribe')
        self.declare_parameter('use_feedback', False)
        self.declare_parameter('use_prompt', True)

        self.model_name = self.get_parameter('model_name').value
        self.language = self.get_parameter('language').value
        self.task = self.get_parameter('task').value
        self.use_prompt = self.get_parameter('use_prompt').value
        self.replace_prompt_whisper = self.get_parameter('replace_prompt_whisper').value
        try:
            self.model = whisper.load_model(self.model_name)
            self.get_logger().info(f"Whisper model '{self.model_name}' loaded on {self.model.device}.")
        except Exception as e:
            self.get_logger().fatal(f"Failed to load whisper model: {e}")
            self.model = None
            return

        self.wip_publisher = self.create_publisher(String, '/speech_recognition/wip_result', 10)
        self.feedback_sub = self.create_subscription(String, '/speech_recognition/wip_feedback', self.feedback_callback, 10)

        self.wip_active = False
        self.processed_index = -1
        self.monitor_thread = None
        self.monitor_thread_running = False
        self.lock = threading.Lock()
        self.feedback_rate = 0.5
    def feedback_callback(self, msg):
        with self.lock:
            try:
                data = json.loads(msg.data)
            except Exception as e:
                self.get_logger().warn(f"Invalid JSON in feedback message: {e}")
                return

            new_wip_active = data.get("active", False)
            self.feedback_rate = data.get("feedback_rate", 0.5)

            if new_wip_active and not self.wip_active:
                self.wip_active = True
                self.processed_index = -1
                if not self.monitor_thread_running:
                    self.monitor_thread_running = True
                    self.monitor_thread = threading.Thread(target=self.monitor_wip_files, daemon=True)
                    self.monitor_thread.start()
            elif not new_wip_active and self.wip_active:
                self.wip_active = False

    def monitor_wip_files(self):
        while self.monitor_thread_running or self.wip_active:
            try:
                wip_files = sorted(glob.glob(os.path.join(self.audio_dir, "temp_wip_output_*.wav")))
                if not self.wip_active and not wip_files:
                    break

                for file_path in wip_files:
                    file_index = int(file_path.split('_')[-1].split('.')[0])
                    with self.lock:
                        if file_index > self.processed_index and os.path.getsize(file_path) >= 1024:
                            time.sleep(0.2)
                            prompt_text = " ".join(self.replace_prompt_whisper) if self.use_prompt else None
                            result = self.model.transcribe(
                                file_path,
                                language=self.language,
                                task=self.task,
                                initial_prompt=prompt_text if prompt_text else None
                            )
                            msg = String()
                            msg.data = result['text'].strip()
                            self.wip_publisher.publish(msg)
                            self.processed_index = file_index

                if not self.wip_active and wip_files and self.processed_index >= int(wip_files[-1].split('_')[-1].split('.')[0]):
                    break

            except Exception as e:
                self.get_logger().error(f"Error in monitoring loop: {e}")

            time.sleep(self.feedback_rate)
        self.monitor_thread_running = False

def main(args=None):
    rclpy.init(args=args)
    node = WIPTranscriber()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()