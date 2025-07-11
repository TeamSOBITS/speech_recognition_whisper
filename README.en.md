<a name="readme-top"></a>

[JA](README.md) | [EN](README.en.md)

[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![License][license-shield]][license-url]

# Speech Rrecognition Whisper

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
        <li><a href="#requirements">Requirements</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#launch-and-usage">Launch and Usage</a></li>
    <li><a href="#parameters">Parameters</a></li>
    <li><a href="#prompt">Prompt</a></li>    
    <li><a href="#milestone">Milestone</a></li>
    <li><a href="#acknowledgements">Acknowledgements</a></li>
  </ol>
</details>

<!-- レポジトリの概要 -->
## Introduction

This is a local speech recognition package.\
It can be used with Action communication, similar to other speech recognition packages.\
Due to its nature, a PC with a GPU is recommended.

> [!NOTE]
> It works on CPU, but there is a slight lag in response.
> Please go online to install.sh.


<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- セットアップ -->
## Getting Started

This section describes how to set up this repository.

### Requirements

First, ensure you have the following environment set up before proceeding to the installation steps.

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
    ```
    colcon build --symlink-install
    ```
    ```
    source ~/colcon_ws/install/setup.sh
    ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- 実行・操作方法 -->
## Launch and Usage

### launch the file
1. In Ubuntu settings, set the input device for sound to the microphone you intend to use.

2. Start the Action Server. Please wait for **Whisper Server is READY and waiting for requests.** to appear before sending any goals.
    ```sh
    ros2 launch speech_recognition_whisper speech_recognition_whisper.launch.py 
    ```

3. Start the Action Client and send the text you want to speak.

    Recorded audio is saved in the sound_file directory.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Parameters

The following parameters can be specified in　[speech_recognition_whisper.launch.py](launch/speech_recognition_whisper.launch.py)

| Parameter | Description | Default Value |
| --- | --- | --- |
| model | [List of Models](https://huggingface.co/collections/openai/whisper-release-6501bba2cf999715fd953013) | small |
| language | [List of Supported Languages](https://github.com/openai/whisper/blob/main/whisper/tokenizer.py) | en |
| task | Specifies the task to execute. You can choose "transcribe" (speech-to-text) or "translate" (translate to English). | transcribe |
| use\_feedback | Whether to enable feedback | False |
| use\_prompt | Whether to use a prompt | False |

To change the model, download it using [install.py](install.py)　and then rewrite the **model** item in [speech_recognition_whisper.launch.py](launch/speech_recognition_whisper.launch.py) to the model you wish to use.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## Prompt

You can specify the "prompt" or context to be given to the model in [whisper_prompt.yaml](prompt/whisper_prompt.yaml).

This can improve the accuracy of recognizing specific words or proper nouns.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- マイルストーン -->
## Milestone

See the [open issues][issues-url] for a full list of proposed features (and known issues).


<!-- 参考文献 -->
## Acknowledgements

* [whisper](https://github.com/openai/whisper)

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
