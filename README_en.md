<a name="readme-top"></a>

[JP](README.md) | [EN](README_en.md)

[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
<!-- [![MIT License][license-shield]][license-url] -->

# speech_recognition_whisper

<!-- 目次 -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#Introduction">Introduction</a>
    </li>
    <li>
      <a href="#Getting Started">Getting Started</a>
      <ul>
        <li><a href="#Requirements">Requirements</a></li>
        <li><a href="#Installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#Launch and Usage">Launch and Usage</a></li>
    <li><a href="#Milestone">Milestone</a></li>
    <li><a href="#Acknowledgements">Acknowledgements</a></li>
  </ol>
</details>


<!-- レポジトリの概要 -->
## Introduction

<!-- [![Product Name Screen Shot][product-screenshot]](https://example.com) -->

A locally running speech recognition package.\
It can be used in the same way as other speech recognition packages, through Service communication.\
GPU PC is recommended due to its nature.

> [!NOTE]
> It works on CPU, but there is a slight lag in response.
> Please go online to install.sh.


<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- セットアップ -->
## Getting Started

This section describes how to set up this repository.

### Requirements



| System  | Version |
| ------------- | ------------- |
| Ubuntu | 20.04 (Focal Fossa) |
| ROS | Noetic Ninjemys |
| Python | 3.8 |

> [!NOTE]
> If you need to install Ubuntu or ROS, please check our [SOBITS Manual](https://github.com/TeamSOBITS/sobits_manual#%E9%96%8B%E7%99%BA%E7%92%B0%E5%A2%83%E3%81%AB%E3%81%A4%E3%81%84%E3%81%A6).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Installation

1. Change directory
   ```sh
   $ cd ~/catkin_ws/src
   ```
2. clone TeamSOBITS/speech_recognition_whisper
   ```sh
   $ git clone https://github.com/TeamSOBITS/speech_recognition_whisper.git
   ```
3. Change directory
   ```sh
   $ cd speech_recognition_whisper/
   ```
4. Install dependent packages
   ```sh
   $ bash install.sh
   ```
5. compile
   ```sh
   $ cd ~/catkin_ws/
   $ catkin_make
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- 実行・操作方法 -->
## Launch and Usage

### launch the file
```sh
roslaunch speech_recognition_whisper speech_recognition_whisper.launch
```
This will start the Server.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Services
 * /speech_recognition (Service: sobits_msgs/SpeechRecognitionWhisper)

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- マイルストーン -->
## Milestone

See the [open issues][issues-url] for a full list of proposed features (and known issues).


<!-- 参考文献 -->
## Acknowledgements

* [ROS Noetic](http://wiki.ros.org/noetic)

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
