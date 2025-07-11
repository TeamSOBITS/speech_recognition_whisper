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
  <summary>目次</summary>
  <ol>
    <li>
      <a href="#概要">概要</a>
    </li>
    <li>
      <a href="#環境構築">環境構築</a>
      <ul>
        <li><a href="#環境条件">環境条件</a></li>
        <li><a href="#インストール方法">インストール方法</a></li>
      </ul>
    </li>
    <li><a href="#実行操作方法">実行・操作方法</a></li>
    <li><a href="#パラメータ">パラメータ</a></li>
    <li><a href="#プロンプト">プロンプト</a></li>
    <li><a href="#マイルストーン">マイルストーン</a></li>
    <li><a href="#参考文献">参考文献</a></li>
  </ol>
</details>


<!-- レポジトリの概要 -->
## 概要

<!-- [![Product Name Screen Shot][product-screenshot]](https://example.com) -->

ローカルで動作する，音声認識パッケージです．\
他の音声認識パッケージと同じように，Action通信で使えます．\
また，性質上GPUのPCを推奨します．

> [!NOTE]
> CPUでも動作しますが，返答に若干ラグがあります．
> install.shまではオンラインで行ってください．


<p align="right">(<a href="#readme-top">上に戻る</a>)</p>


<!-- 環境構築 -->
## 環境構築

ここで，本レポジトリのセットアップ方法について説明します．

### 環境条件

まず，以下の環境を整えてから，次のインストール段階に進んでください．

| System  | Version |
| ------------- | ------------- |
| Ubuntu | 22.04 (Jammy Jellyfish) |
| ROS | Humble Hawksbill |
| Python | 3.10 |

<p align="right">(<a href="#readme-top">上に戻る</a>)</p>

### インストール方法

1. ROSの`src`フォルダに移動します．
   ```sh
   cd ~/colcon_ws/src/
   ```
2. 本レポジトリをcloneします．
   ```sh
   git clone -b humble-devel https://github.com/TeamSOBITS/speech_recognition_whisper.git
   ```
3. レポジトリの中へ移動します．
   ```sh
   cd speech_recognition_whisper/
   ```
4. 依存パッケージをインストールします．
   ```sh
   bash install.sh
   ```
5. パッケージをコンパイルします．
   ```sh
   cd ~/colcon_ws/
   ```
   ```sh
   colcon build --symlink-install
   ```
   ```sh
   source ~/colcon_ws/install/setup.sh
   ```


<p align="right">(<a href="#readme-top">上に戻る</a>)</p>

<!-- 実行・操作方法 -->
## 実行・操作方法
1. Ubuntuの設定で，サウンドの入力デバイスを使用するマイクに設定します．

2. Action Serverを起動します．
```sh
ros2 launch speech_recognition_whisper speech_recognition_whisper.launch.py
```
3. Action Clientを起動します．

<p align="right">(<a href="#readme-top">上に戻る</a>)</p>

## パラメータ
[speech_recognition_whisper.launch.py](launch/speech_recognition_whisper.launch.py)では以下のパラメータを指定できます．

| パラメータ | 説明 | デフォルト値 |
| --- | --- | --- |
| model | [モデル一覧](https://huggingface.co/collections/openai/whisper-release-6501bba2cf999715fd953013) | small |
| launguage | [対応言語一覧](https://github.com/openai/whisper/blob/main/whisper/tokenizer.py) | en |
| task | 実行するタスクを指定します。"transcribe"（文字起こし）または"translate"（英語への翻訳）が選択できます。 | transcribe |
| use_feedback | フィードバックを有効にするかどうか | False |
| use_prompt | プロンプトを用いるかどうか | False |

モデルを変更する場合は[install.py](install.py)でダウンロードし，[speech_recognition_whisper.launch.py](launch/speech_recognition_whisper.launch.py)の**model**の項目を使用するモデルに書き換えてください．

 <p align="right">(<a href="#readme-top">上に戻る</a>)</p>
 
## プロンプト
[whisper_prompt.yaml](prompt/whisper_prompt.yaml)でモデルに与える「プロンプト」や文脈を指定します。

これにより、特定の単語や固有名詞の認識精度を向上させることができます。

 <p align="right">(<a href="#readme-top">上に戻る</a>)</p>

<!-- マイルストーン -->
## マイルストーン

現時点のバッグや新規機能の依頼を確認するために[Issueページ](issues-url) をご覧ください．

<p align="right">(<a href="#readme-top">上に戻る</a>)</p>

<!-- 参考文献 -->
## 参考文献

* [whisper](https://github.com/openai/whisper)

<p align="right">(<a href="#readme-top">上に戻る</a>)</p>

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
