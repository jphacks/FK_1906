# プレゼンテーションチェッカー

## 製品概要
### プレゼンテーション Tech

### 背景（製品開発のきっかけ、課題等）
プレゼンテーションにおいて、**視線**や**抑揚**はとても大事なものである。    
しかし、実際に自分が**視線**や**抑揚**をうまく使えているか客観的に判断することは難しい。     
そこで、私達はこれらのプレゼンテーションスキルを客観的に判断できるアプリを考えた。   

### 製品説明（具体的な製品の説明）

### 特長

#### 1. プレゼンテーションを視線や抑揚に基づいて採点できる

#### 2. 視線推定技術(NEC遠隔視線推定API)を用いて、プレゼンターの視線を解析
- 左右 => 左右に視線に偏りがないか 
- 上下 => 下を向いていないか
- 分布 => 全体を見渡せているか

#### 3. フーリエ変換を用いて、プレゼンターの声の抑揚を解析
- 声の大小
- 声のトーン

### 使用方法

1. プレゼンテーションを撮影し、動画をアップロード
2. **視線**、**抑揚**の観点から採点結果が表示される
3. プレゼンターの**視線**データを表示した動画をダウンロードすることもできる

### 解決出来ること
プレゼンテーションスキルの向上

### 今後の展望
現在、プレゼンテーションのスコアは経験則に基づいたパラメータを設定している。
今後は、機械学習を用いたパレメータ設定ができるようにしたい。

## 開発内容・開発技術
### 活用した技術
#### API・データ

* NEC遠隔視線推定API 
* WebAudioAPI

#### フレームワーク・ライブラリ・モジュール
* Flask
* [requierments.txt](https://github.com/jphacks/FK_1906/blob/master/requierments.txt)


### 独自開発技術（Hack Dayで開発したもの）
#### 2日間に開発した独自の機能・技術
* フーリエ変換を用いた声の抑揚の抽出
