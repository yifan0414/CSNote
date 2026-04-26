1.  如果您之前从来没有用过 Git，推荐您阅读 Pro Git 的前几章，或者完成像 Learn Git Branching这样的教程。重点关注 Git 命令和数据模型相关内容；
    
2.  Fork 本课程网站的仓库
    
3.  将版本历史可视化并进行探索
    
    ```bash
     git log --all --graph --decorate
    ```
    
    ![[attachments/7febabee71e0f0f7a65132f144c03408_MD5.png]]
    
4.  是谁最后修改了 README.md文件？（提示：使用 git log 命令并添加合适的参数）
    
    ```bash
    git log README.md
    ```
    
    ![[attachments/8925e68a6e7caa5851908177ce2a1e4f_MD5.png]]
    
5.  最后一次修改_config.yml 文件中 collections: 行时的提交信息是什么？（提示：使用 git blame 和 git show）
    
    ```bash
     git blame _config.yml | grep collections
    ```
    
    ![[attachments/bf2aada32584133bd0bebe05a6262b66_MD5.png]]
    
    ```bash
     git show a88b4eac
    ```
    
    ![[attachments/c225a0daab5432d8471c3aa40a9fbcc8_MD5.png]]
    
6.  使用 Git 时的一个常见错误是提交本不应该由 Git 管理的大文件，或是将含有敏感信息的文件提交给 Git 。尝试向仓库中添加一个文件并添加提交信息，然后将其从历史中删除 ( 这篇文章也许会有帮助)；
7.  首先提交一些敏感信息
    
    ```bash
     echo "password123">my_password
     git add .
     git commit -m "add password123 to file"
     git log HEAD
    ```
    
    ![[attachments/89abcd91f0ace5ad297b2ad0d2893f30_MD5.png]]
    
8.  使用`git filter-branch`清除提交记录
    
    ```bash
     git filter-branch --force --index-filter\
     'git rm --cached --ignore-unmatch ./my_password' \
     --prune-empty --tag-name-filter cat -- --all
    ```
    
    文件已经删除![[attachments/a313d9b3183ab76070456e07efbca1d4_MD5.png]]提交记录已经删除![[attachments/5449a101a5b8af2535a62c35ad178c3a_MD5.png]]
    
9.  从 GitHub 上克隆某个仓库，修改一些文件。当您使用 git stash 会发生什么？当您执行 git log –all –oneline 时会显示什么？通过 git stash pop 命令来撤销 git stash 操作，什么时候会用到这一技巧？![[attachments/70edd152f42e7b3664162abe6f94200a_MD5.png]]![[attachments/32f092b8a91c37db8acf94b4e4c8e2ea_MD5.png]]![[attachments/d817d77c35bcd7e8af2ee4dd11b6f59b_MD5.png]]![[attachments/160672d93eedb196cb1462e940110e4d_MD5.png]]

10. 与其他的命令行工具一样，Git 也提供了一个名为 ~/.gitconfig 配置文件 (或 dotfile)。请在 ~/.gitconfig 中创建一个别名，使您在运行 git graph 时，您可以得到 git log –all –graph –decorate –oneline 的输出结果；

```bash
     [alias]
         graph = log --all --graph --decorate --oneline
```
    
11. 您可以通过执行 git config –global core.excludesfile ~/.gitignore_global 在 ~/.gitignore_global 中创建全局忽略规则。配置您的全局 gitignore 文件来自动忽略系统或编辑器的临时文件，例如 .DS_Store；
    
```bash
     git config --global core.excludesfile ~/.gitignore .DS_Store
```
    
12. 克隆 本课程网站的仓库，找找有没有错别字或其他可以改进的地方，在 GitHub 上发起拉取请求（Pull Request）； 首先 fork 本网站仓库，然后克隆 fork 后的仓库
    
```bash
     git clone https://github.com/hanxiaomax/missing-semester.git
```
    

在本地进行修改后，提交到 fork 后的仓库，然后[发起 PR](https://github.com/missing-semester/missing-semester/pulls)
    
![[attachments/e2d7238f3cddd4e9360821b210198eec_MD5.png]]