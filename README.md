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
      <a href="#セットアップ">セットアップ</a>
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

本リポジトリは，OpenAIの[whisper](https://github.com/openai/whisper)および
[faster-whisper](https://github.com/SYSTRAN/faster-whisper)の自動音声認識（ASR）機能を
ROS2のアクション通信に対応させたものです．

ローカル環境で動作します．

> [!NOTE]
> CPUでも動作しますが，返答に若干ラグがあります．
> install.shまではオンラインで行ってください．


<p align="right">(<a href="#readme-top">上に戻る</a>)</p>


<!-- セットアップ -->
## セットアップ

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
| model | 実行する Whisper モデル *1 | small |
| language | 音声認識を行う言語．[対応言語一覧](https://github.com/openai/whisper/blob/main/whisper/tokenizer.py) | en |
| task | 実行するタスク．"transcribe"（文字起こし）または"translate"（英語への翻訳）を選択可能． | transcribe |
| use_prompt | プロンプトを用いるかどうか | False |
| use_feedback | 音声認識の途中結果(フィードバック)を有効にするかどうか | True |
| backend | 使用するバックエンド: "whisper" または "faster-whisper" | whisper |


*1 サイズが小さい順に``tiny``, ``base``, ``small``, ``medium``, ``large``, ``large-v2``, ``large-v3``, ``large-v3-turbo``があります．
Faster-Whisperも同じモデルサイズに対応しますが，推論は高速かつ省メモリです．
詳細は[モデル一覧](https://huggingface.co/collections/openai/whisper-release-6501bba2cf999715fd953013)を参照してください．

- モデルを変更する場合は[install.py](install.py)でダウンロードし，[speech_recognition_whisper.launch.py](launch/speech_recognition_whisper.launch.py)の**model**の項目を使用するモデルに書き換えてください．


以下はFeedbackに関するパラメータです．\
``use_feedback``が``True``のときのみ有効です．\
以下の値を変更しても最終認識結果には影響しません．

| パラメータ | 説明 | デフォルト値 |
| - | - | - |
| vad_name | フィードバックの際に使用する音声アクティビティ検出(VAD)の手法．VADの使用によりフィードバックの認識精度が向上する．``None``を選択するとVADを使用せずAction Clientで指定したFeedback Rateの秒数ごとに音声認識を行う． | ten_vad |
| hop_size | VADモデルが音声データを処理するチャンク（断片）のサイズ．160 or 256を選択可能．値が小さいほど応答性が上がるが，CPU負荷が増える | 256 |
| threshold | VADモデルが音声を検出するための確率のしきい値．値を高くすると誤検出が減るが，かすれた声や小さな声が無視される可能性がある | 0.5 |
| min_wipe_duration | ノイズを無視し音声認識するために必要な声の最短の長さ．VADが発話と認識した区間がこの秒数より短い場合，ノイズとして無視され音声認識の処理を行わない．| 0.2 | 

 <p align="right">(<a href="#readme-top">上に戻る</a>)</p>
 
## プロンプト
[whisper_prompt.yaml](prompt/whisper_prompt.yaml)でモデルに与える「プロンプト」や文脈を指定します．

プロンプトで特定の単語やフレーズ，固有名詞をモデルに事前に教えることで，モデルの予測を誘導し認識精度が向上します．

 <p align="right">(<a href="#readme-top">上に戻る</a>)</p>

<!-- マイルストーン -->
## マイルストーン

現時点のバッグや新規機能の依頼を確認するために[Issueページ](issues-url) をご覧ください．

<p align="right">(<a href="#readme-top">上に戻る</a>)</p>

<!-- 参考文献 -->
## 参考文献

* [Whisper](https://github.com/openai/whisper)
* [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper)  
* [TEN VAD](https://github.com/TEN-framework/ten-vad)

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
