package com.wrecktheline.linearsbox

import android.R
import android.app.Activity
import android.content.Context
import android.content.Intent
import android.nfc.NfcAdapter
import android.nfc.Tag
import android.os.Bundle
import android.util.Log
import android.view.ViewGroup
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.maxieds.MifareClassicToolLibrary.MifareClassicDataInterface
import com.maxieds.MifareClassicToolLibrary.MifareClassicTag
import com.maxieds.MifareClassicToolLibrary.MifareClassicToolLibrary
import com.wrecktheline.linearsbox.databinding.ActivityMainBinding
import org.apache.commons.compress.compressors.bzip2.BZip2CompressorInputStream
import java.io.ByteArrayInputStream


fun String.decodeHex(): ByteArray {
    check(length % 2 == 0) { "Must have an even length" }

    return chunked(2)
        .map { it.toInt(16).toByte() }
        .toByteArray()
}

class MainActivity : AppCompatActivity(), MifareClassicDataInterface {

    private lateinit var binding: ActivityMainBinding
    private var currentlyTagScanning = false
    private val TAG = "com.wrecktheline.linearsbox"
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        MifareClassicToolLibrary.InitializeLibrary(this)
//        MifareClassicToolLibrary.StartLiveTagScanning(this)
        currentlyTagScanning = true

        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)



//        val arr: ByteArray = byteArrayOf(66, 90, 104, 57, 49, 65, 89, 38, 83, 89, -12, 92, 125, -79, 0, 34, 68, 127, -1, -16, 64, 64, 68, 64, 64, 64, 68, 119, -1, -1, -4, 65, 64, 64, 64, 64, 64, 64, 64, 96, 64, 64, -64, 64, 64, 64, 64, 64, 64, 65, 64, 64, 2, 124, 29, -50, 113, -70, -84, 69, 64, 50, 24, 19, 24, -47, 60, 84, 0, 0, 0, 0, 34, -89, -122, 65, -90, -102, -92, -12, -98, -111, -95, -96, 104, -45, 64, 0, 12, -12, 80, 69, 79, -39, 19, 83, 73, 63, 83, 73, -22, 49, 13, 6, 64, -56, 105, -112, 26, 3, 1, 53, 74, -103, 68, 49, 26, 104, 52, 52, 98, 0, 3, 64, 0, 61, 71, 73, 69, 83, -36, 1, -15, -56, 5, 105, 97, 2, -83, 42, -74, 0, 114, 123, 56, 104, -30, 1, -108, -93, 32, -30, -64, -87, -103, 84, -46, 69, 90, 0, -54, -107, -69, 86, 86, 86, 9, 85, -11, 0, -54, 14, 16, 12, 111, -43, 85, 102, -75, 93, 74, -86, -85, -41, -82, -107, 90, 117, 64, 106, 3, 84, 6, -117, 90, -32, -39, 102, 102, 101, -11, -64, 72, 36, 41, 32, 2, -41, 17, 60, -57, -11, -9, -108, 8, 119, 121, 68, 34, -103, 51, -54, 9, 99, 17, 40, 15, 118, -19, 120, -108, 61, -89, 59, -11, -24, -61, -11, -61, 34, -92, -22, -85, 90, 26, -94, -88, -108, 70, -91, 84, -110, 85, 21, 106, -76, 88, -116, -115, 37, 26, -99, 104, -75, 84, 0, -117, 112, -102, 46, 89, 83, 108, -14, -18, -53, -4, -68, -4, -1, 25, -69, 49, -43, -73, 29, 22, -74, 26, 121, 118, 20, -9, 33, 120, 69, -52, -102, 56, 84, -72, -93, 38, -84, 86, 100, -74, 19, -111, 12, -47, -25, -55, 112, -66, -88, -116, 85, 37, 23, -110, 57, 68, -59, -50, -91, 108, 105, 57, 13, 18, 32, 0, 0, 0, 8, 45, -102, 78, 80, 76, 82, 20, -86, -98, 97, 51, 38, -45, 67, -104, 100, 110, -25, -27, -26, -25, -17, 64, 58, -44, -26, -128, 50, -85, -62, 1, -29, -86, -86, -38, 3, 114, -86, -86, -38, 3, 0, 48, 6, -128, 27, 0, 61, 64, 50, -86, -85, 118, -107, -103, 77, -64, 31, -67, -65, -99, -101, -68, -82, 107, 49, -76, 11, 91, -35, 103, -32, -24, 14, 32, -37, 11, -123, 7, 35, 10, -47, 16, -127, 107, 105, -104, -59, -116, -125, 50, 58, 23, -106, -60, -70, -14, 109, -121, 106, -94, -49, -14, -55, 78, -114, -108, -83, -98, 124, 50, 40, -31, -83, 107, -123, -104, -119, -87, 106, 16, 10, 112, 113, 0, -127, 92, -10, -70, -8, 31, -31, -117, 8, -62, 112, 17, 105, -35, 98, 107, -84, -56, 18, 72, 33, 12, -28, -15, 56, 51, 98, -33, 90, -19, 23, -106, 104, -95, -86, 22, -119, -85, 81, 8, 101, 94, 54, -120, -64, 95, -2, -86, -31, -74, -39, 84, -18, -47, 3, 3, -120, 61, -113, -102, 52, 25, 125, 49, -30, -108, -114, 87, 60, -62, 50, 96, 35, -63, -12, 73, 53, -49, 115, 83, 85, -46, -29, -49, -101, 51, 111, -45, 37, 85, 127, -128, 48, 10, 127, -59, -36, -111, 78, 20, 36, 61, 23, 31, 108, 64)
//        val in_stream = ByteArrayInputStream(arr)
//        val bz_stream = BZip2CompressorInputStream(in_stream)
//        val bytes = bz_stream.readBytes()
//
//        // Example of a call to a native method
//        var out = ""
//        for (each in stringFromJNI(bytes)) {
//            out += each.toInt().toString()+" "
//        }
//
//        binding.sampleText.text = out

//        val fin: InputStream = Files.newInputStream(Paths.get("archive.tar.bz2"))
//        val `in` = BufferedInputStream(fin)
//        val out: OutputStream = Files.newOutputStream(Paths.get("archive.tar"))
//        val bzIn = BZip2CompressorInputStream(`in`)
//        val buffer = ByteArray(buffersize)
//        var n = 0
//        while (-1 != bzIn.read(buffer).also { n = it }) {
//            out.write(buffer, 0, n)
//        }
//        out.close()
//        bzIn.close()
    }

    // implement these functions in the client activity:
    override fun onResume() {
        super.onResume()
        if (currentlyTagScanning) {
            MifareClassicToolLibrary.StartLiveTagScanning(this)
        }
    }

    override fun onPause() {
        if (currentlyTagScanning) {
            MifareClassicToolLibrary.StopLiveTagScanning(this)
        }
        super.onPause()
    }


    override fun onNewIntent(intent: Intent?) {

        if (intent == null || intent.action == null) {
            return
        }
        if ((intent.action == NfcAdapter.ACTION_TAG_DISCOVERED) || (intent.action == NfcAdapter.ACTION_TECH_DISCOVERED)) {
            Toast.makeText(this, "start reading card", Toast.LENGTH_SHORT).show()

            val nfcTag = intent.getParcelableExtra<Tag>(NfcAdapter.EXTRA_TAG)
            if (MifareClassicTag.CheckMifareClassicSupport(nfcTag) != 0) {
                println("The discovered NFC device is not a Mifare Classic tag.")
                return
            }
            println("got here")


            try {
                val mfcTag = MifareClassicTag.Decode(
                    nfcTag,
                    arrayOf("FFFFFFFFFFFF", "A0A1A2A3A4A5", "D3F7D3F7D3F7"),
                    false
                )
                println(mfcTag)
                var data = ""
                val count = mfcTag.GetSectorCount()
                for (i in 0..(count - 1)) {
                    val sector = mfcTag.GetSectorByIndex(i)
                    var start_idx = if (i == 0) 1 else 0

                    for (j in start_idx..(sector.sectorBlockCount - 2)) {
                        val e = sector.sectorBlockData[j]
                        Log.d(TAG, e)
                        data += e
                    }
                }

                val arr: ByteArray = data.decodeHex()
                val in_stream = ByteArrayInputStream(arr)
                val bz_stream = BZip2CompressorInputStream(in_stream)
                val bytes = bz_stream.readBytes()

                // Example of a call to a native method
                val flag = getFlag(bytes)

                binding.sampleText.text = String(flag)
            } catch (e: Exception) {
                // handler
                binding.sampleText.text = "read error"

                Toast.makeText(this, "read error", Toast.LENGTH_SHORT).show()
            }



        }
        // process other intents
    }

    /**
     * A native method that is implemented by the 'linearsbox' native library,
     * which is packaged with this application.
     */
    external fun getFlag(arr: ByteArray): ByteArray

    companion object {
        // Used to load the 'linearsbox' library on application startup.
        init {
            System.loadLibrary("linearsbox")
        }
    }

    override fun RegisterNewIntent(mfcIntent: Intent?) {
//        TODO("Not yet implemented")
    }

    override fun GetApplicationContext(): Context {
//        TODO("Not yet implemented")
        return this.applicationContext
    }

    override fun GetApplicationActivity(): Activity {
//        TODO("Not yet implemented")
        return this
    }

    override fun PostTagScanKeyMapProgress(position: Int, total: Int) {
//        TODO("Not yet implemented")
    }

    override fun PostTagScanSectorReadProgress(position: Int, total: Int) {
//        TODO("Not yet implemented")
    }
}