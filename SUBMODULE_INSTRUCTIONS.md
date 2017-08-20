# GIT submodule instructions

Tutorial on how to use any submodule in any repository like here the [SimplifiedGmailApi](https://github.com/AnonymerNiklasistanonym/SendGmailSimplified).

(*If you want to learn more visit [this](https://github.com/blog/2104-working-with-submodules) site*)

## Joining a project using submodules

If you just clone the repository there will be an empty folder where the submodule is normally located.

To get it's content use either this at the `git clone` process:

```
git clone --recursive <project url>
```

Or if you already cloned the repository use:

```
git submodule update --init --recursive
```



Have fun programming! :smiley:



*PS: If you want to use this submodule do not forget to activate the API in the main project script*