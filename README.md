# 概要

- netkeiba.comで公開されている地方競馬のデータをスクレイピングして、データベースを作成します。
- Streamlitを用いて簡易GUIを実装しています。[^1]
[^1]: データ取得部分は完成。データ表示部分は試行錯誤中ですが、ポートフォリオとして公開しています。

# 使い方

## Pythonの準備
- Pythonをダウンロードします。
- ターミナルでプロジェクトのルートフォルダに移動し、venvの中に必要モジュールをインストールします。
   ```
   python -m venv .venv
   source .venv/bin/activate  # macOS
   # .venv/Scripts/activate   # Windows
   python -m pip install -r required.txt
   ```
## MongoDBの準備
- MongoDBをダウンロードします。
- nar.db/modules/database/connect_mongo_db.pyの`####`部分に、MongoDBのユーザー名とパスワードを書きます。[^2]
  
   <img width="745" alt="スクリーンショット 2024-01-29 15 16 23" src="https://github.com/LifeOnFloor/nar.db/assets/119148510/1108ce5b-a03f-4717-9c5b-ad05b5d69675">
[^2]: TODO: セキュリティ的によくない書き方のようなので、後で修正したいです。

## nar.dbの起動
- `python st.py`とすると、ブラウザが起動します。
- 最初はなにもデータが入ってないので、以下のような画面が出てきます。

<img width="940" alt="スクリーンショット 2024-01-29 14 42 31" src="https://github.com/LifeOnFloor/nar.db/assets/119148510/ab538879-4fef-4718-b80d-0e10168de8fa">


- `database`ページで取得するデータを指定できます。

<img width="1439" alt="スクリーンショット 2024-01-29 14 43 51" src="https://github.com/LifeOnFloor/nar.db/assets/119148510/5af6c379-062b-4fa7-94a1-dc605af09f8e">

>[!CAUTION]
>[スクレイピング]
>netkeiba.comに負荷がかからないように、節度あるアクセス頻度にしてください。
