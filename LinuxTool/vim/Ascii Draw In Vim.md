# Description
>DrawIt! : Ascii drawing plugin: lines, ellipses, arrows, fills, and more!

```
 ____                     ___ _   _
|  _ \ _ __ __ ___      _|_ _| |_| |
| | | | '__/ _` \ \ /\ / /| || __| |
| |_| | | | (_| |\ V  V / | || |_|_|
|____/|_|  \__,_| \_/\_/ |___|\__(_)
```

DrawIt is a plugin which allows one to draw lines left, right, up, down, and along both slants. Optionally one may "cap" the lines with arrowheads.  One may change the horizontal, vertical, slant, and crossing characters to whichever characters one wishes.

# Install

You can enter this offical [web](https://www.vim.org/scripts/script.php?script_id=40) to get the vim plugin.

Or you can type the following instruction in command line to install the vim plugin file.

```
wget -O DrawIt.vba.gz http://www.vim.org/scripts/download_script.php?src_id=21108
```

To activate the plugin in vim, you also need to execute remaining instruction. 

```
$vim DrawIt.vba.gz

// in vim normal mode
:so %
:q
```


# The usage of DrawIt

> You must only use the tool in Vim

Firstly, use `\di` to enter the Drawit mode in Vim, and you can use `\ds` to quit this mode.

In this mode, your `arrow key` transfer to a pen, when you move the `arrow key`, the  trace will be left on the screen. But you can use `hjkl` to move the cursor dangingly.

## All features
```
   <left>       move and draw left  
   <right>      move and draw right, inserting lines/space as needed  
   <up>         move and draw up, inserting lines/space as needed  
   <down>       move and draw down, inserting lines/space as needed  
   <s-left>     move left  
   <s-right>    move right, inserting lines/space as needed  
   <s-up>       move up, inserting lines/space as needed  
   <s-down>     move down, inserting lines/space as needed  
   <space>      toggle into and out of erase mode  
   >            draw -> arrow  
   <            draw <- arrow  
   ^            draw ^  arrow  
   v            draw v  arrow  
   <pgdn>       replace with a \, move down and right, and insert a \  
   <end>        replace with a /, move down and left,  and insert a /  
   <pgup>       replace with a /, move up   and right, and insert a /  
   <home>       replace with a \, move up   and left,  and insert a \  
   \>           draw fat -> arrow  
   \<           draw fat <- arrow  
   \^           draw fat ^  arrow  
   \v           draw fat v  arrow  
   \a           draw arrow based on corners of visual-block  
   \b           draw box using visual-block selected region  
   \e           draw an ellipse inside visual-block  
   \f           fill a figure with some character  
   \h           create a canvas for \a \b \e \l  
   \l           draw line based on corners of visual block  
   \s           adds spaces to canvas  
   <leftmouse>  select visual block  
   <s-leftmouse>  drag and draw with current brush (register)  
   \ra ... \rz  replace text with given brush/register  
   \pa ...      like \ra ... \rz, except that blanks are considered  
                to be transparent
```


# Personal Experience 

## How to Seclect the region
1. you can use `<C-V>` enter the region visual mode, then use the `hjkl` to seclect specific region.
2. you can also drag the mouse to seclect the specific region.

## How to BOX a sentence

![gjDYFp|600](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/gjDYFp.png)

1. you can use `\b` to boxes the sentence
2. you can create a box firstly, Then use the `R` which can enter the `replace mode` to replace the space character.

![WN1kR9|600](https://picture-suyifan.oss-cn-shenzhen.aliyuncs.com/uPic/WN1kR9.png)



# Some example

![[i386 2.3 Registers#^bgqkxa]]

![[i386 2.3 Registers#^dkjzy1]]