# Local development

## Conda environment

Run `xuanxin` from **usao**, not base conda:

```bash
conda activate usao
pip install -e .   # once, or after pulling code changes
xuanxin diary -i /home/wukong/xx-diary -o /home/wukong/output_folder -home wu-99.com --page-size 20
```

Or without activating:

```bash
/home/wukong/miniconda3/envs/usao/bin/xuanxin diary -i /home/wukong/xx-diary -o /home/wukong/output_folder -home wu-99.com --page-size 20
```

Using base conda's `xuanxin` or system `python3` may hit missing dependencies (`frontmatter`, etc.) or an outdated install.
