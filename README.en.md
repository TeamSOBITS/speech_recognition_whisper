<a name="readme-top"></a>

[JA](README.md) | [EN](README.en.md)

[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![License][license-shield]][license-url]

# Speech Recognition Whisper

<!-- 目次 -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#introduction">Introduction</a>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#launch-and-usage">Launch and Usage</a></li>
    <li><a href="#parameters">Parameters</a></li>
    <li><a href="#prompt">Prompt</a></li>    
    <li><a href="#milestones">Milestones</a></li>
    <li><a href="#references">References</a></li>
  </ol>
</details>

<!-- レポジトリの概要 -->
## Introduction

This repository provides the automatic speech recognition (ASR) capabilities of OpenAI's [whisper](https://github.com/openai/whisper) and [faster-whisper](https://github.com/SYSTRAN/faster-whisper) adapted for ROS2 action communication.

It runs in a local environment.

> [!NOTE]
> It can run on a CPU, but there will be a slight delay in the response.
> Please perform the steps up to `install.sh` online.


<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- セットアップ -->
## Getting Started

This section describes how to set up this repository.

### Prerequisites

First, ensure you have the following environment set up before proceeding with the installation.

| System  | Version |
| ------------- | ------------- |
| Ubuntu | 22.04 (Jammy Jellyfish) |
| ROS | Humble Hawksbill |
| Python | 3.10 |

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Installation

1. Navigate to your ROS2 src folder.
    ```sh
    cd ~/colcon_ws/src/
    ```
2. Clone this repository．
    ```sh
    git clone -b humble-devel https://github.com/TeamSOBITS/speech_recognition_whisper.git
    ```
3. Move into the repository directory.
    ```sh
    cd speech_recognition_whisper/
    ```
4. Install dependent packages
    ```sh
    bash install.sh
    ```
5. Compile the package.
    ```sh
    cd ~/colcon_ws/
    ```
    ```sh
    colcon build --symlink-install
    ```
    ```sh
    source ~/colcon_ws/install/setup.sh
    ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- 実行・操作方法 -->
## Launch and Usage

1. In Ubuntu settings, set the input device for sound to the microphone you intend to use.

2. Start the Action Server. Please wait for **Whisper Server is READY and waiting for requests.** to appear before sending any goals.
    ```sh
    ros2 launch speech_recognition_whisper speech_recognition_whisper.launch.py 
    ```

3. Start the Action Client and send the text you want to speak.
    - timeout_sec: Duration (in seconds) to keep the microphone open. If a negative value is provided, it continues to return feedback until a cancel request is sent.
    - silent_mode: If set to `true`, the start and end notification sounds will not be played.
    - feedback_rate: Specifies the frequency of intermediate speech recognition results when `use_feedback` is `True` and `vad_name` is `None`.

    ```sh
    ros2 action send_goal /speech_recognition sobits_interfaces/action/SpeechRecognition "timeout_sec: 5
    silent_mode: false
    feedback_rate: 0.5" -f
    ```
    Recorded audio is saved in the sound_file directory.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Parameters
The following parameters can be set in [speech_recognition_whisper.launch.py](launch/speech_recognition_whisper.launch.py).

| Parameter | Description | Default Value |
| :--- | :--- | :--- |
| **`model`** | The Whisper model to use. *1 | `small` |
| **`language`** | The language for speech recognition. See the [list of supported languages](https://github.com/openai/whisper/blob/main/whisper/tokenizer.py). | `en` |
| **`task`** | The task to perform. You can choose `"transcribe"` for transcription or `"translate"` for translation into English. | `transcribe` |
| **`use_prompt`** | Whether to use a prompt to guide the model's predictions. | `False` |
| **`backend`** | The backend to use: "whisper" or "faster-whisper" | whisper |
| device | Computing device to use (`cpu` or `cuda`). If left empty, it automatically selects GPU if available, otherwise falls back to CPU.| "" |
| **`compute_type`** | The computation type when using faster-whisper: "float16", "int8_float16", or "int8" | float16 |
| **`mic_volume`** | Sets the microphone input volume as a percentage. When finish program, the original volume will be restored. e.g., "100" | `"100"` |
| **`use_feedback`** | Whether to enable work-in-progress (WIP) speech recognition feedback. | `True` |

*1 Models are available in increasing order of size: `tiny`, `base`, `small`, `medium`, `large`, `large-v2`, `large-v3`, and `large-v3-turbo`. Faster-Whisper supports the same model sizes but offers faster inference and lower memory usage. For more details, refer to the [model list](https://huggingface.co/collections/openai/whisper-release-6501bba2cf999715fd953013).

- To change the model, first download it using [install.py](install.py), then change the `model` parameter in [speech_recognition_whisper.launch.py](launch/speech_recognition_whisper.launch.py) to the desired model name.


The following parameters are for feedback and are only enabled when `use_feedback` is set to `True`. Changing these values does not affect the final recognition result.

| Parameter | Description | Default Value |
| :--- | :--- | :--- |
| **`vad_name`** | The Voice Activity Detection (VAD) method used for feedback. Using VAD improves the accuracy of feedback recognition. Selecting `None` disables VAD, and speech recognition will be performed at the interval specified by the Action Client's Feedback Rate. | `ten_vad` |
| **`hop_size`** | The size of the audio data chunk (fragment) processed by the VAD model. You can choose between `160` and `256`. A smaller value increases responsiveness but also raises CPU load. | `256` |
| **`threshold`** | The probability threshold for the VAD model to detect a voice. A higher value reduces false positives but might cause faint or quiet voices to be ignored. | `0.5` |
| **`min_wipe_duration`** | The minimum length of a voice segment needed to trigger speech recognition. If the VAD recognizes a voice segment that is shorter than this value in seconds, it's ignored as noise, and the speech recognition process isn't started. | `0.2` |
| **`extra_audio_duration_sec`** | Additional audio time to include before and after the audio for each feedback. | `0.2` |
| max_speech_duration | Maximum duration (in seconds) to segment a single utterance.| 30.0 |

The following are parameters related to echo cancellation.

| Parameter | Description | Default Value |
| :--- | :--- | :--- |
| **`use_echo_cancel`** | It helps prevent the microphone from picking up audio from the speakers. | `False` |
| **`noise_suppression`** | Toggles the noise suppression feature. | `False` |
| **`analog_gain_control`** |  Automatically adjusts the microphone input volume at the hardware level. It suppresses loud sounds and amplifies quiet ones to prevent clipping and improve clarity. | `False` |
| **`digital_gain_control`** |  Automatically adjusts the input volume at the software level. It modifies the amplitude after the audio data has been digitized. | `False` |

Parameters other than `model_name`, `backend`, `compute_type`, `use_feedback`, `vad_name`, and those related to echo cancellation can be changed after the launch file is started.



Example: To change `min_wipe_duration` to 0.1
  ```sh
  ros2 param set /whisper_server min_wipe_duration 0.1
  ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## Prompt

In [whisper_prompt.yaml](prompt/whisper_prompt.yaml), you can specify the "prompt" or context to provide to the model.

By pre-training the model with specific words, phrases, or proper nouns through a prompt, you can guide its predictions and improve recognition accuracy.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- マイルストーン -->
## Milestone

See the [open issues][issues-url] for a full list of proposed features (and known issues).


<!-- 参考文献 -->
## References

* [Whisper](https://github.com/openai/whisper)
* [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper)  
* [TEN VAD](https://github.com/TEN-framework/ten-vad)
* [module-echo-cancel](https://www.freedesktop.org/wiki/Software/PulseAudio/Documentation/User/Modules/?utm_source=chatgpt.com#module-echo-cancel)


<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/TeamSOBITS/speech_recognition_whisper.svg?style=for-the-badge
[contributors-url]: https://github.com/TeamSOBITS/speech_recognition_whisper/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/TeamSOBITS/speech_recognition_whisper.svg?style=for-the-badge
[forks-url]: https://github.com/TeamSOBITS/speech_recognition_whisper/network/members
[stars-shield]: https://img.shields.io/github/stars/TeamSOBITS/speech_recognition_whisper.svg?style=for-the-badge
[stars-url]: https://github.com/TeamSOBITS/speech_recognition_whisper/stargazers
[issues-shield]: https://img.shields.io/github/issues/TeamSOBITS/speech_recognition_whisper.svg?style=for-the-badge
[issues-url]: https://github.com/TeamSOBITS/speech_recognition_whisper/issues
[license-shield]: https://img.shields.io/github/license/TeamSOBITS/speech_recognition_whisper.svg?style=for-the-badge
[license-url]: LICENSE

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
<!-- []:  -->
