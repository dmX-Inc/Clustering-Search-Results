﻿using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;
using System.Runtime.Serialization.Formatters.Binary;
using System.IO;

namespace Clustering_research_tool
{
     public partial class Form1 : Form
    {
        Form2 F;
        List<string> input;
        public static List<string[]> TestData = new List<string[]>();
        static int formwidth, formheight;
        public static bool firstTxtEnter;
        public static bool txtEntered;
        public static bool listChanged;
        bool fileopened;
        public Form1()
        {
            InitializeComponent();
            input = new List<string>();
            F = new Form2();
            formwidth = F.Size.Width;
            formheight = F.Size.Height;
            button3.Enabled = false;
            firstTxtEnter = true;
            txtEntered = false;
            listChanged = false;
            saveToolStripMenuItem.Enabled = false;
            fileopened = false;
        }

        private void richTextBox1_TextChanged(object sender, EventArgs e)
        {
        }

        private void button1_Click(object sender, EventArgs e)
        {
            if (richTextBox1.Text != "")
            {
                input.Add(richTextBox1.Text);
                TextOperations.InitParams(input);
                listBox1.Items.Add(TextOperations.ts[TextOperations.ts.Count - 1]);
                richTextBox1.Text = "";
                txtEntered = true;
                if (input.Count >= 3 || TestData.Count > 0)
                {
                    button3.Enabled = true;
                    saveToolStripMenuItem.Enabled = true;
                }
            }
        }

        private void button2_Click(object sender, EventArgs e)
        {
            input = new List<string>();
            listBox1.Items.Clear();
            if (!fileopened)
            {
                txtEntered = false;
                saveToolStripMenuItem.Enabled = false;
                if (firstTxtEnter && TestData.Count < 1) button3.Enabled = false;
            }
            listChanged = true;
            
        }

        private void button3_Click(object sender, EventArgs e)
        {
            //Список конвертируется в массив
            if (txtEntered || fileopened)
            {
                string[] temp = new string[input.Count];
                for (int i = 0; i < temp.Length; i++)
                {
                    temp[i] = input[i];
                }
                if (listChanged || firstTxtEnter)
                {
                    if (!fileopened)
                    {
                        TestData.Add(temp);
                        listChanged = true;
                    }
                }
                if (firstTxtEnter && !fileopened)
                {
                    firstTxtEnter = false;
                }
            }
            F = new Form2();
            //Задаются необходимые для обработки текстов параметры и формируется частотная матрица
            TextOperations.TagNullifier();
            TextOperations.FormMatrix();
            F.ShowDialog();
            
            if (txtEntered || fileopened)
            {
                listChanged = false;
            }
            fileopened = false;
        }

        public static int GetForm2Width
        {
            get { return formwidth; }
            set { formwidth = value; }
        }

        private void saveToolStripMenuItem_Click(object sender, EventArgs e)
        {
            saveFileDialog1.ShowDialog();
        }

        private void saveFileDialog1_FileOk(object sender, CancelEventArgs e)
        {
            BinaryFormatter bf = new BinaryFormatter();
            bool edot = false;
            FileStream fs;
            for (int i = 0; i < saveFileDialog1.FileName.Length; i++)
            {
                if (saveFileDialog1.FileName[i] == '.')
                {
                    edot = true;
                }
            }
            if (edot)
            {
                fs = new FileStream(saveFileDialog1.FileName, FileMode.Create, FileAccess.Write);
            }
            else
            {
                fs = new FileStream(saveFileDialog1.FileName + ".clst", FileMode.Create, FileAccess.Write);
            }
            string[] temp = new string[input.Count];
            for (int i = 0; i < temp.Length; i++)
            {
                temp[i] = input[i];
            }
            if (listChanged || firstTxtEnter)
            {
                TestData.Add(temp);
            }
            else
            {
                TestData[TestData.Count - 1] = temp;
            }
            bf.Serialize(fs, TestData[TestData.Count - 1]);
            fs.Close();
        }

        private void openToolStripMenuItem_Click(object sender, EventArgs e)
        {
            openFileDialog1.ShowDialog();
        }

        private void openFileDialog1_FileOk(object sender, CancelEventArgs e)
        {
            input = new List<string>();
            listBox1.Items.Clear();
            BinaryFormatter bf = new BinaryFormatter();
            FileStream fs = new FileStream(openFileDialog1.FileName, FileMode.Open, FileAccess.Read);
            TestData.Add((string[])bf.Deserialize(fs));
            fileopened = true;
            button3.Enabled = true;
            saveToolStripMenuItem.Enabled = true;
            TextOperations.InitParams(TestData[TestData.Count - 1]);
            listChanged = true;
        }

        public static int GetForm2Height
        {
            get { return formheight; }
            set { formheight = value; }
        }
    }
}
