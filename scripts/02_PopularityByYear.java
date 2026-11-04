import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.TimeZone;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.LongWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.hadoop.mapreduce.Reducer;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.input.TextInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;
import org.apache.hadoop.mapreduce.lib.output.TextOutputFormat;

/**
 * MapReduce (Java) - Popularity theo (movieId, year) tren HDFS.
 *
 * Input : /recsys/ratings_csv/part-00000.csv   (userId,movieId,rating,timestamp)
 * Output: /recsys/out/popularity_by_year/      (movieId,year -> count)
 *
 * Key la Text dang "movieId,year" - su dung comparator mac dinh (lexicographic).
 * Dung de chung minh 2 duong xu ly (MapReduce Java vs Spark SQL) cho cung ket qua:
 * quality gate G3 trong ke hoach thuc nghiem.
 */
public class PopularityByYear {

  public static class PopMapper extends Mapper<Object, Text, Text, IntWritable> {
    private static final SimpleDateFormat SDF = new SimpleDateFormat("yyyy");
    static {
      SDF.setTimeZone(TimeZone.getTimeZone("UTC"));
    }

    private final Text outKey = new Text();
    private final IntWritable outVal = new IntWritable(1);

    @Override
    protected void map(Object key, Text value, Context context)
        throws IOException, InterruptedException {
      // input: userId,movieId,rating,timestamp
      String[] p = value.toString().split(",");
      if (p.length < 4) return;
      int movieId;
      long ts;
      try {
        movieId = Integer.parseInt(p[1].trim());
        ts = Long.parseLong(p[3].trim());
      } catch (NumberFormatException e) {
        return;
      }
      int year = Integer.parseInt(SDF.format(new java.util.Date(ts * 1000L)));
      outKey.set(movieId + "," + year);
      context.write(outKey, outVal);
    }
  }

  public static class PopReducer extends Reducer<Text, IntWritable, Text, IntWritable> {
    private final IntWritable outVal = new IntWritable();

    @Override
    protected void reduce(Text key, Iterable<IntWritable> values, Context context)
        throws IOException, InterruptedException {
      int sum = 0;
      for (IntWritable v : values) sum += v.get();
      outVal.set(sum);
      context.write(key, outVal);
    }
  }

  public static void main(String[] args) throws Exception {
    if (args.length < 2) {
      System.err.println("Usage: PopularityByYear <input> <output>");
      System.exit(2);
    }
    Configuration conf = new Configuration();
    Job job = Job.getInstance(conf, "PopularityByYear");
    job.setJarByClass(PopularityByYear.class);
    job.setMapperClass(PopMapper.class);
    job.setCombinerClass(PopReducer.class);
    job.setReducerClass(PopReducer.class);
    job.setOutputKeyClass(Text.class);
    job.setOutputValueClass(IntWritable.class);
    // Map output value phai khop voi reducer input (IntWritable), khong phai output value
    job.setMapOutputKeyClass(Text.class);
    job.setMapOutputValueClass(IntWritable.class);

    FileInputFormat.addInputPath(job, new Path(args[0]));
    FileOutputFormat.setOutputPath(job, new Path(args[1]));

    boolean ok = job.waitForCompletion(true);
    System.out.println("JOB_STATUS=" + (ok ? "SUCCESS" : "FAILED"));
    System.exit(ok ? 0 : 1);
  }
}
